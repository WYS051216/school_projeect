"""DeepSeek 大模型调用封装（能力证据抽取）。"""
import json
import os

import httpx
from dotenv import load_dotenv

# 从 backend/.env 读取密钥，不写进代码、不进 git
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

SYSTEM_PROMPT = (
    "你是一名资深技术简历顾问。用户会提供若干篇学习笔记或项目经历材料，"
    "请你从中提炼出「适合直接写进技术简历的能力条目」。"
    "要求："
    "1. 条目要概括、宏观，是简历级别的技能，不是零碎知识点；"
    "例如不要写「Redis 的 AOF 持久化」，而要写成「Redis（掌握持久化、主从复制、哨兵高可用与集群）」。"
    "2. 同类技术要合并：例如「智能指针、移动语义、RAII」应合并为一条「C++ 现代特性」。"
    "3. description 用简历语言写：以「熟悉/掌握/了解」开头，说明掌握程度、覆盖要点、以及能做什么。"
    "4. 数量宁少勿滥，把碎片合并成有分量的条目，整体 5~15 条为宜。"
    "严格只输出一个 JSON 对象，形如："
    '{"abilities": [{"kind": "skill|project|achievement", "name": "能力名称", '
    '"description": "简历式描述", "source": "来源文档标题"}]}。'
    "不要输出任何 JSON 之外的文字。"
    "kind 只能是 skill（技能）、project（项目）、achievement（成果）之一；"
    "name 简短（15 字以内）；source 填这条能力出自哪些文档的标题，多个用顿号分隔，无法确定就留空。"
)


def _build_user_prompt(docs):
    parts = []
    for d in docs[:15]:  # 最多 15 篇，防止超出模型上下文
        content = (d.get("content") or "")[:3000]  # 每篇最多 3000 字符
        parts.append(f"【{d.get('title', '')}】\n{content}")
    return "以下是用户的材料：\n\n" + "\n\n---\n\n".join(parts)


def _recover_partial_json(content):
    """JSON 被 max_tokens 截断时，尽力提取已完整解析的数组元素。"""
    start = content.find("[")
    if start < 0:
        return []
    content = content[start:]
    decoder = json.JSONDecoder()
    items = []
    i = 1
    n = len(content)
    while i < n:
        while i < n and content[i] in " \t\n\r,":
            i += 1
        if i >= n or content[i] == "]":
            break
        try:
            obj, end = decoder.raw_decode(content, i)
            items.append(obj)
            i = end
        except json.JSONDecodeError:
            break
    return items


def _parse_abilities_json(content):
    """解析 DeepSeek 返回，兼容数组 / {"abilities": [...]}，并容错截断。"""
    content = content.strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = _recover_partial_json(content)

    if isinstance(parsed, dict):
        abilities = parsed.get("abilities", [])
    elif isinstance(parsed, list):
        abilities = parsed
    else:
        abilities = []
    return abilities if isinstance(abilities, list) else []


def extract_abilities(docs):
    """调用 DeepSeek，从 docs（[{"title","content"}]）中抽取能力证据。

    返回 [{"kind","name","description","source"}...]；出错时抛 RuntimeError。
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，请检查 backend/.env")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(docs)},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }

    resp = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
        trust_env=False,  # 绕过系统代理直连
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek 调用失败（{resp.status_code}）：{resp.text[:300]}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    abilities = _parse_abilities_json(content)
    if not abilities:
        raise RuntimeError("DeepSeek 未返回有效结果，请减少选择的文档数量后重试")

    result = []
    for item in abilities:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "kind": item.get("kind", "skill"),
                "name": str(item.get("name", "")).strip() or "未命名能力",
                "description": str(item.get("description", "")).strip(),
                "source": str(item.get("source", "")).strip(),
            }
        )
    return result


RESUME_SKILLS_PROMPT = (
    "你现在是一位资深的大厂技术 HR 和高级简历指导专家。"
    "用户会提供目标岗位和一份原始技术栈（能力证据）列表。"
    "请围绕目标岗位，把这些技术栈高度压缩并重构为「可以直接粘贴到单页简历上」的专业技能模块。"
    "严格约束条件："
    "1. 模块化排版：使用加粗的分类标题（如「C++ 与架构设计」「系统与网络并发」等）独立成行，"
    "绝对禁止在每一条技能前重复分类名称。"
    "2. 极度精简：每个分类下保留 2~3 个核心项目符号（Bullet Points），每条控制在 1 行以内（最多 50 个中文字符）。"
    "3. 高密度合并：将同维度的技术点强行合并，例如将「智能指针、右值引用、Lambda」统一概括为"
    "「熟练运用 C++11-20 现代特性」；将「进程生命周期、僵尸进程、资源回收」合并为一句话。"
    "4. 剔除冗余：删掉「了解、熟悉」等口水话连用，直接突出核心能力；删去过度基础的名词（如「三次握手」「代码段」）。"
    "输出格式要求（严格参照此模板生成，分类标题用 Markdown 加粗，方括号 [...] 是占位符，"
    "请替换为实际提炼的、真实具体的技能内容，不要输出占位符本身）："
    "**C++ 与架构设计**"
    ""
    "熟练运用 C++11-20 现代特性与 STL 组件，具备 RAII 与防御性编程意识。"
    ""
    "[提炼合并后的技能点 2]"
    ""
    "**系统与网络并发**"
    ""
    "[提炼合并后的技能点 1]"
    ""
    "[提炼合并后的技能点 2]"
    "只输出专业技能模块正文，不要任何额外解释。"
)


def generate_resume_skills(abilities, target_position):
    """根据能力证据 + 目标岗位，生成简历「专业技能」栏目文本。

    abilities: [{"name","description","kind"}...]
    返回纯文本；出错时抛 RuntimeError。
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，请检查 backend/.env")

    lines = []
    for i, a in enumerate(abilities, 1):
        desc = (a.get("description") or "").strip()
        lines.append(f"{i}. {a.get('name', '')}：{desc}" if desc else f"{i}. {a.get('name', '')}")
    ability_text = "\n".join(lines) or "（无）"

    user_content = (
        f"目标岗位：{target_position}\n\n"
        f"用户已确认的能力证据：\n{ability_text}\n\n"
        "请据此生成简历「专业技能」模块内容。"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": RESUME_SKILLS_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    resp = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
        trust_env=False,  # 绕过系统代理直连
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek 调用失败（{resp.status_code}）：{resp.text[:300]}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    if not content:
        raise RuntimeError("DeepSeek 未返回有效结果，请重试")
    return content
