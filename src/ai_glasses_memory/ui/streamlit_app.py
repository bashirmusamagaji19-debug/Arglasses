from __future__ import annotations

import streamlit as st

from ai_glasses_memory.config import get_settings
from ai_glasses_memory.services.memory_store import MemoryStore
from ai_glasses_memory.services.ocr import create_ocr_provider
from ai_glasses_memory.services.pipeline import MemoryPipeline
from ai_glasses_memory.services.uploads import save_input_image


def get_pipeline() -> MemoryPipeline:
    settings = get_settings()
    return MemoryPipeline(
        MemoryStore(settings.db_path),
        ocr_provider=create_ocr_provider(settings.ocr_provider),
    )


st.set_page_config(page_title="AI 眼镜记忆助手", layout="wide")
st.title("AI 眼镜实时视觉记忆助手")
st.caption("手机摄像头第一视角输入 -> 模拟 OCR / 模拟 VLM -> 视觉记忆时间线。")

pipeline = get_pipeline()

left, right = st.columns([1, 1])

with left:
    st.subheader("当前输入")
    camera_image = st.camera_input("用手机摄像头拍一张第一视角照片")
    uploaded_file = st.file_uploader("或上传一张图片作为备用", type=["png", "jpg", "jpeg", "webp"])
    selected_image = camera_image or uploaded_file
    if selected_image is not None:
        st.image(selected_image, caption="当前画面", use_container_width=True)
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
            st.caption(item.scene_summary)

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
