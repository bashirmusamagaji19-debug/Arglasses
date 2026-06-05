from __future__ import annotations

import streamlit as st

from ai_glasses_memory.config import get_settings
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.ocr import create_ocr_provider
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.search import create_search_provider
from ai_glasses_memory.services.uploads import save_input_image
from ai_glasses_memory.services.vlm import create_vlm_provider


def get_pipeline() -> MemoryPipeline:
    settings = get_settings()
    store = MemoryStore(settings.db_path)
    return MemoryPipeline(
        store,
        ocr_provider=create_ocr_provider(settings.ocr_provider),
        vlm_provider=create_vlm_provider(
            settings.vlm_provider,
            base_url=settings.vlm_base_url,
            api_key=settings.vlm_api_key,
            model=settings.vlm_model,
            max_tokens=settings.vlm_max_tokens,
            timeout_seconds=settings.vlm_timeout_seconds,
            max_image_width=settings.vlm_max_image_width,
        ),
        search_provider=create_search_provider(
            settings.search_provider,
            store=store,
            vector_db_path=settings.vector_db_path,
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
        ),
    )


st.set_page_config(page_title="AI 眼镜记忆助手", layout="wide")
st.title("AI 眼镜实时视觉记忆助手")
st.caption("手机摄像头第一视角输入 -> 模拟 OCR / 模拟 VLM -> 视觉记忆时间线。")

settings = get_settings()
ocr_provider_name = settings.ocr_provider.strip().lower()
st.info(f"当前 OCR 模式：{ocr_provider_name}")
if ocr_provider_name == "paddleocr":
    st.warning("PaddleOCR 首次识别会加载模型，可能需要 10-30 秒；后续会更快。")
vlm_provider_name = settings.vlm_provider.strip().lower()
st.info(f"当前 VLM 模式：{vlm_provider_name}")
if vlm_provider_name == "openai_compatible":
    st.warning("真实 VLM 每次提交都会产生一次模型调用，请控制提交频率和图片大小。")

search_provider_name = settings.search_provider.strip().lower()
embedding_provider_name = settings.embedding_provider.strip().lower()
st.info(f"当前检索模式：{search_provider_name}；当前 Embedding 模式：{embedding_provider_name}")
if search_provider_name == "vector" and embedding_provider_name == "hash":
    st.warning("Hash embedding 只用于验证向量检索架构，不是真正语义模型；需要更好效果请切换到 sentence_transformers。")

pipeline = get_pipeline()

left, right = st.columns([1, 1])

with left:
    st.subheader("当前输入")
    camera_image = st.camera_input("用手机摄像头拍一张第一视角照片")
    uploaded_file = st.file_uploader("或上传一张图片作为备用", type=["png", "jpg", "jpeg", "webp"])
    selected_image = camera_image or uploaded_file
    if selected_image is not None:
        st.image(selected_image, caption="当前画面", width="stretch")
    question = st.text_input("输入问题", value="我刚才看到了什么？")
    submitted = st.button("提交问题", type="primary")

with right:
    st.subheader("本次回答")
    if submitted:
        image_path = save_input_image(selected_image)
        result = pipeline.ask(question=question, image_path=image_path)
        st.markdown("**回答**")
        st.write(result.answer)
        st.markdown("**OCR 文本**")
        st.write(result.ocr_text)
        st.markdown("**场景摘要**")
        st.write(result.scene_summary)
        st.markdown("**延迟统计（ms）**")
        st.json(result.latency_ms)
    else:
        st.info("拍照或上传图片并提交问题后，这里会显示模拟回答、OCR 文本、场景摘要和延迟统计。")

st.divider()

search_col, timeline_col = st.columns([1, 2])

with search_col:
    st.subheader("历史检索")
    keyword = st.text_input("搜索关键词", value="")
    if keyword.strip():
        search_results = pipeline.search_memories(keyword.strip())
        st.write(f"找到 {len(search_results)} 条记录")
        for item in search_results:
            st.markdown(f"**{item.created_at.strftime('%Y-%m-%d %H:%M:%S')}**")
            st.write(item.question)
            st.markdown("**回答**")
            st.write(item.answer)
            st.caption(item.scene_summary)
    st.subheader("记忆管理")
    keep_latest = st.number_input("只保留最近 N 条", min_value=1, max_value=500, value=50, step=1)
    if st.button("裁剪记忆"):
        deleted = pipeline.prune_memories(int(keep_latest))
        st.session_state["memory_management_message"] = f"已删除 {deleted} 条记忆。"
        st.rerun()
    if st.button("去重记忆"):
        deleted = pipeline.dedupe_memories()
        st.session_state["memory_management_message"] = f"已删除 {deleted} 条重复记忆。"
        st.rerun()
    confirm_clear = st.checkbox("确认清空全部记忆")
    if st.button("清空全部记忆", disabled=not confirm_clear):
        deleted = pipeline.clear_memories()
        st.session_state["memory_management_message"] = f"已删除 {deleted} 条记忆。"
        st.rerun()
    if "memory_management_message" in st.session_state:
        st.success(st.session_state.pop("memory_management_message"))

with timeline_col:
    st.subheader("记忆时间线")
    memories = pipeline.list_memories()
    if not memories:
        st.info("还没有记忆记录。")
    for memory in memories:
        with st.expander(f"{memory.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {memory.question}"):
            st.markdown("**回答**")
            st.write(memory.answer)
            st.markdown("**场景摘要**")
            st.write(memory.scene_summary)
            st.markdown("**OCR 文本**")
            st.write(memory.ocr_text)
            st.markdown("**延迟统计（ms）**")
            st.json(memory.latency_ms)
            if st.button("删除这条记忆", key=f"delete-memory-{memory.id}"):
                deleted = pipeline.delete_memory(memory.id)
                st.session_state["memory_management_message"] = f"已删除 {deleted} 条记忆。"
                st.rerun()
