# Bug 21：工程包装材料落后于 RAG 实现

## 现象

项目已经实现 Chroma RAG 历史记忆问答，但部分文档仍停留在早期阶段：

- `docs/phase3-search.md` 仍把 Chroma / FAISS 描述成后续替换路径。
- `docs/vector-search.md` 主要描述 SQLite vector provider，没有清楚说明当前默认 Chroma RAG。
- 面试材料只有 30 秒 demo 脚本，缺少简历 bullet、常见问答和 2 分钟讲解稿。

这会导致一个问题：代码已经具备更强能力，但 README、阶段文档和面试材料不能帮助别人快速理解当前系统。

## 根因

这是典型的工程包装滞后问题。项目迭代过程中，功能推进顺序是：

```text
lightweight search
-> SQLite vector provider
-> Chroma provider
-> RAG answer provider
```

但部分文档只记录到了中间阶段，没有在 Chroma 成为默认 provider 后及时更新。对于作品集项目来说，这会影响演示可信度：面试官看到文档和代码不一致，会怀疑项目边界是否清晰。

## 修复

本次修复做了三件事：

1. 更新 `docs/phase3-search.md`，把当前检索阶段描述为“历史记忆检索与 RAG”，明确 lightweight、SQLite vector 和 Chroma 三种 provider 的定位。
2. 更新 `docs/vector-search.md`，说明当前默认是 Chroma RAG，SQLite vector provider 是保留的本地向量方案。
3. 新增面试包装材料：
   - `docs/interview/resume-bullets.md`
   - `docs/interview/interview-qa.md`
   - `docs/interview/demo-script-2min.md`

## 面试复盘表达

> 我在功能迭代后发现，项目文档仍然停留在早期向量检索阶段，而代码已经升级到了 Chroma RAG。如果不修正，面试官或协作者会看到文档和实现不一致。  
> 所以后来我把工程包装作为单独阶段处理：更新架构文档、补齐 demo 脚本、简历 bullet 和面试问答。这个过程让我意识到，作品集项目不是只写代码，还要让别人能快速看懂系统为什么这么设计、当前做到哪里、后续还能怎么扩展。

## 经验

- 功能升级后要同步更新阶段文档，尤其是架构默认值和 provider 选择。
- 面试项目需要“代码 + demo + 文档 + 调试记录”一起交付。
- Debug log 不只记录运行时 bug，也可以记录工程交付中的信息不一致问题。
