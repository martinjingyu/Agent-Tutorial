"""
跨源事实核验 Pipeline — 脚手架模板

本文件包含 Pipeline 的类定义框架和 mock LLM 调用函数。
你需要实现所有组件，使其能够处理 materials/ 目录下的输入文本，
并输出 output/fact_table.json。

运行方式: python pipeline.py
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime


# ============================================================
# Mock LLM 调用（模拟真实 LLM，包含故意设计的缺陷）
# ============================================================

def mock_llm_call(prompt: str) -> str:
    """
    模拟 LLM 调用。
    
    注意：这个 mock 函数包含故意设计的缺陷，你需要通过
    Checker 组件来检测和修复这些问题。
    
    缺陷列表：
    1. 日期解析只支持 "YYYY-MM-DD" 格式
    2. 有时会返回格式不一致的 JSON
    3. 置信度计算不考虑来源权威度
    """
    # 模拟 LLM 的格式漂移
    if "extract facts" in prompt.lower():
        # 有时返回格式不一致的 JSON
        if "date" in prompt.lower() and "2026/03/16" in prompt:
            return '{"date": "2026/03/16", "format": "slash_separated"}'
        return '{"status": "ok", "facts": []}'
    
    if "validate" in prompt.lower():
        return '{"is_valid": true, "confidence": 0.8}'
    
    return '{"status": "ok"}'


# ============================================================
# 组件定义（你需要实现以下所有类）
# ============================================================

class FactItem:
    """
    统一的事实条目模型。
    
    你需要设计这个类的 schema，使其能够：
    1. 存储不同事件类型的事实（动态维度）
    2. 追踪来源和置信度
    3. 支持冲突标记
    """
    
    def __init__(self, fact_id: str, dimension: str, value: Any,
                 confidence: float, sources: List[str]):
        self.fact_id = fact_id
        self.dimension = dimension
        self.value = value
        self.confidence = confidence
        self.sources = sources
        self.status = "pending"  # pending | verified | conflict | rejected
        self.conflict_detail: Optional[Dict] = None
        self.note: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        # TODO: 实现序列化
        pass


class FactExtractor:
    """
    从单条文本中提取事实。
    
    第一步：从预定义的 4 个维度提取（事件时间、地点、参与方、关键数字）
    第二步：自动发现需要提取的维度（不硬编码）
    """
    
    def __init__(self):
        # TODO: 初始化提取器
        pass
    
    def extract(self, text: str, source_id: str,
                dimensions: Optional[List[str]] = None) -> List[FactItem]:
        """
        从文本中提取事实。
        
        Args:
            text: 输入文本
            source_id: 来源标识（如 "M1"）
            dimensions: 需要提取的维度列表。None 表示自动发现。
        
        Returns:
            提取的事实列表
        """
        # TODO: 实现提取逻辑
        pass
    
    def discover_dimensions(self, texts: List[str]) -> List[str]:
        """
        自动发现需要提取的事实维度。
        
        第二步使用。分析所有输入文本，决定需要提取哪些维度。
        
        Args:
            texts: 所有输入文本列表
        
        Returns:
            维度名称列表
        """
        # TODO: 实现维度发现
        pass


class CrossValidator:
    """
    跨源交叉验证。
    
    对多个来源提取的同一维度事实进行交叉验证，
    计算一致性分数，标记冲突。
    """
    
    def __init__(self):
        # TODO: 初始化验证器
        pass
    
    def validate(self, facts_by_source: Dict[str, List[FactItem]]) -> List[FactItem]:
        """
        跨源验证事实。
        
        Args:
            facts_by_source: {source_id: [FactItem, ...]}
        
        Returns:
            验证后的事实列表（包含置信度和冲突标记）
        """
        # TODO: 实现交叉验证
        pass


class ConflictResolver:
    """
    冲突分级与解决。
    
    将冲突标记为以下等级：
    1. 明确矛盾（同一事实有不同值，来源权威度相近）
    2. 疑似矛盾（值不同，但可能因表述方式不同）
    3. 信息互补（不同来源提供同一事实的不同侧面）
    """
    
    def __init__(self):
        # TODO: 初始化冲突解决器
        pass
    
    def resolve(self, facts: List[FactItem]) -> List[FactItem]:
        """
        解决事实间的冲突。
        
        Args:
            facts: 待解决冲突的事实列表
        
        Returns:
            解决冲突后的事实列表
        """
        # TODO: 实现冲突解决
        pass


class Checker:
    """
    质量检测与定向修复。
    
    检测以下问题：
    1. 幻觉（事实与多数来源矛盾）
    2. 格式漂移（输出格式不一致）
    3. 置信度过低（需要标记或丢弃）
    
    修复策略：
    1. 定向重跑（只修复失败的步骤）
    2. 标记保留（对低置信度事实做标记而非删除）
    """
    
    def __init__(self):
        # TODO: 初始化检查器
        pass
    
    def check(self, facts: List[FactItem]) -> List[Dict]:
        """
        检测事实列表中的质量问题。
        
        Returns:
            问题列表，每个问题包含：
            - type: 问题类型（hallucination | format_drift | low_confidence）
            - severity: 严重程度（low | medium | high）
            - fact_id: 关联的事实 ID
            - description: 问题描述
        """
        # TODO: 实现质量检测
        pass
    
    def repair(self, facts: List[FactItem], issues: List[Dict]) -> List[FactItem]:
        """
        根据检测到的问题进行定向修复。
        
        Args:
            facts: 原始事实列表
            issues: Checker 检测到的问题列表
        
        Returns:
            修复后的事实列表
        """
        # TODO: 实现定向修复
        pass


class FactVerificationPipeline:
    """
    主 Pipeline。
    
    编排以下组件：
    1. FactExtractor — 事实提取
    2. CrossValidator — 交叉验证
    3. ConflictResolver — 冲突解决
    4. Checker — 质量检测与修复
    """
    
    def __init__(self):
        self.extractor = FactExtractor()
        self.validator = CrossValidator()
        self.conflict_resolver = ConflictResolver()
        self.checker = Checker()
        self.stats = {
            "total_inputs": 0,
            "events_detected": 0,
            "facts_extracted": 0,
            "conflicts_detected": 0,
            "hallucinations_flagged": 0,
            "format_issues_corrected": 0,
            "checker_passes": 0,
            "checker_failures": 0,
            "repair_actions": 0,
        }
    
    def run(self, inputs: Dict[str, str]) -> Dict:
        """
        运行完整 Pipeline。
        
        Args:
            inputs: {source_id: text, ...}
        
        Returns:
            符合 output/fact_table.json 格式的完整输出
        """
        # TODO: 实现 Pipeline 编排
        pass


# ============================================================
# 主函数
# ============================================================

def load_materials(materials_dir: str = "materials") -> Dict[str, str]:
    """加载 materials/ 目录下的所有输入文本"""
    inputs = {}
    if not os.path.exists(materials_dir):
        print(f"Warning: {materials_dir} not found, using sample data")
        return _get_sample_inputs()
    
    for filename in sorted(os.listdir(materials_dir)):
        if filename.endswith(".txt"):
            filepath = os.path.join(materials_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                source_id = filename.replace(".txt", "")
                inputs[source_id] = f.read()
    
    return inputs


def _get_sample_inputs() -> Dict[str, str]:
    """返回示例输入（用于测试）"""
    return {
        "M1": "AuroraTech (NASDAQ: AURT) announced acquisition of DataWeave Inc. for $2.8 billion.",
        "M2": "AuroraTech buys DataWeave for $2.8B. Expected to close Q3 2026.",
    }


def main():
    """主函数"""
    print("=" * 60)
    print("跨源事实核验 Pipeline")
    print("=" * 60)
    
    # 加载输入
    inputs = load_materials()
    print(f"\nLoaded {len(inputs)} input sources")
    
    # 运行 Pipeline
    pipeline = FactVerificationPipeline()
    result = pipeline.run(inputs)
    
    # 输出结果
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fact_table.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults written to {output_path}")
    print(f"Pipeline stats: {json.dumps(pipeline.stats, indent=2)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
