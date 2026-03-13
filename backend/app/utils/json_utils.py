# src/utils/json_utils.py
import json
import re
from typing import Any, Dict, Optional, Union

class JsonUtils:
    @staticmethod
    def parse_json(json_str: str, fix_format: bool = True) -> Union[Dict, list, Any]:
        """
        解析JSON字符串，可选择尝试修复常见格式问题
        
        Args:
            json_str: JSON字符串
            fix_format: 是否尝试修复格式问题
            
        Returns:
            解析后的JSON对象(字典或列表)
            
        Raises:
            ValueError: 如果JSON无法解析
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if not fix_format:
                raise ValueError(f"JSON解析错误: {str(e)}") from e
                
            # 尝试修复并重新解析
            fixed_json = JsonUtils.fix_json_format(json_str)
            if fixed_json:
                return JsonUtils.parse_json(fixed_json, fix_format=False)
            else:
                raise ValueError(f"无法修复JSON格式: {str(e)}") from e
    
    @staticmethod
    def fix_json_format(json_str: str) -> Optional[str]:
        """
        尝试修复常见的JSON格式问题
        
        Args:
            json_str: 可能格式不正确的JSON字符串
            
        Returns:
            修复后的JSON字符串，如果无法修复则返回None
        """
        # 0. 去除JSON开头可能存在的非JSON文本
        try:
            # 找到第一个 { 或 [ 的位置作为JSON开始
            start_brace = json_str.find('{')
            start_bracket = json_str.find('[')
            
            # 如果两者都存在，使用最靠前的那个
            if start_brace >= 0 and start_bracket >= 0:
                start_pos = min(start_brace, start_bracket)
            # 如果只有一个存在
            elif start_brace >= 0:
                start_pos = start_brace
            elif start_bracket >= 0:
                start_pos = start_bracket
            else:
                start_pos = -1
                
            # 如果找到了起始位置且不在第一个字符
            if start_pos > 0:
                json_str = json_str[start_pos:]
                try:
                    json.loads(json_str)
                    return json_str
                except:
                    pass  # 继续尝试其他修复方法
        except:
            pass
            
        # 1. 修复属性名没有引号的问题
        try:
            # 使用正则表达式为没有引号的键添加双引号
            # 匹配没有双引号的键，后面跟着冒号
            fixed = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)
            json.loads(fixed)  # 测试是否可解析
            return fixed
        except:
            pass
            
        # 2. 处理单引号而不是双引号的情况
        try:
            # 将单引号替换为双引号，但跳过嵌套的引号
            fixed = json_str.replace("'", '"')
            json.loads(fixed)
            return fixed
        except:
            pass
            
        # 3. 处理尾部逗号问题
        try:
            # 删除对象和数组末尾多余的逗号
            fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
            json.loads(fixed)
            return fixed
        except:
            pass
            
        # 4. 处理JavaScript注释
        try:
            # 删除单行注释
            fixed = re.sub(r'//.*?(\n|$)', r'\1', json_str)
            # 删除多行注释
            fixed = re.sub(r'/\*.*?\*/', '', fixed, flags=re.DOTALL)
            json.loads(fixed)
            return fixed
        except:
            pass
        
        # 5. 处理可能被包裹在其他文本中的JSON
        try:
            # 尝试匹配最长的可能是JSON的部分
            match = re.search(r'({.*})', json_str, re.DOTALL)
            if match:
                candidate = match.group(1)
                json.loads(candidate)
                return candidate
        except:
            pass
            
        return None

    @staticmethod
    def safe_json_load(file_path: str, default_value: Any = None) -> Any:
        """
        安全地从文件加载JSON，处理可能出现的异常
        
        Args:
            file_path: JSON文件路径
            default_value: 如果加载失败返回的默认值
            
        Returns:
            解析后的JSON对象，或者默认值
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return JsonUtils.parse_json(content)
        except (IOError, ValueError) as e:
            print(f"无法加载JSON文件 {file_path}: {str(e)}")
            return default_value

    @staticmethod
    def safe_json_dump(data: Any, file_path: str, indent: int = 2) -> bool:
        """
        安全地将数据保存为JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 保存的文件路径
            indent: JSON缩进
            
        Returns:
            是否成功保存
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            print(f"无法保存JSON到 {file_path}: {str(e)}")
            return False

    @staticmethod
    def extract_json_from_text(text: str) -> Optional[str]:
        """
        从文本中提取JSON字符串
        
        Args:
            text: 可能包含JSON的文本
            
        Returns:
            提取的JSON字符串，如果未找到则返回None
        """
        # 检查输入是否为空
        if not text or not isinstance(text, str):
            return None
            
        # 先尝试整个文本是否是有效的JSON
        try:
            json.loads(text)
            return text
        except:
            pass
            
        # 尝试找到最长且最有可能是JSON的部分
        
        # 尝试检测并处理常见的LLM输出格式如：```json ... ```
        json_code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
        for block in json_code_blocks:
            try:
                json.loads(block.strip())
                return block.strip()
            except:
                # 尝试修复并验证
                fixed = JsonUtils.fix_json_format(block.strip())
                if fixed:
                    return fixed
        
        # 尝试查找 { 和匹配的 } 之间的内容（处理嵌套）
        # 从最长的可能JSON开始尝试
        json_candidates = []
        
        # 找到所有的 { 位置
        open_positions = [pos for pos, char in enumerate(text) if char == '{']
        
        for start_pos in open_positions:
            # 从此位置开始找匹配的右括号
            depth = 0
            for i in range(start_pos, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:  # 找到匹配的右括号
                        json_candidates.append(text[start_pos:i+1])
                        break
        
        # 类似地处理数组
        open_positions = [pos for pos, char in enumerate(text) if char == '[']
        
        for start_pos in open_positions:
            # 从此位置开始找匹配的右括号
            depth = 0
            for i in range(start_pos, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                    if depth == 0:  # 找到匹配的右括号
                        json_candidates.append(text[start_pos:i+1])
                        break
                        
        # 按长度从大到小排序候选项（更长的JSON更有可能是完整的）
        json_candidates.sort(key=len, reverse=True)
        
        # 尝试解析每个候选项
        for candidate in json_candidates:
            try:
                json.loads(candidate)
                return candidate
            except:
                # 尝试修复并验证
                fixed = JsonUtils.fix_json_format(candidate)
                if fixed:
                    return fixed
        
        # 回退到旧方法：使用简单正则表达式
        try:
            # 尝试查找 { 和 } 之间的内容
            matches = re.findall(r'({.*?})', text, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    # 尝试修复并验证
                    fixed = JsonUtils.fix_json_format(match)
                    if fixed:
                        return fixed
            
            # 尝试查找 [ 和 ] 之间的内容
            matches = re.findall(r'(\[.*?\])', text, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    # 尝试修复并验证
                    fixed = JsonUtils.fix_json_format(match)
                    if fixed:
                        return fixed
        except:
            pass
        
        return None

    @staticmethod
    def safe_parse_json(input_data: Union[str, Dict, list, Any], debug_prefix: str = "") -> Union[Dict, list, Any]:
        """
        安全解析JSON，具有完整的错误处理。如果输入已经是字典或列表，则直接返回。
        集成了所有常见的JSON解析错误处理步骤，避免在代码中重复try-except块。
        
        Args:
            input_data: 要解析的数据，可以是字符串或已经是字典/列表的对象
            debug_prefix: 调试输出的前缀，用于区分不同的调用位置
            
        Returns:
            解析后的对象(字典或列表)，如果解析失败则返回空字典 {}
        """
        # 如果已经是字典或列表类型，直接返回
        if isinstance(input_data, (dict, list)):
            return input_data
            
        # 检查空输入
        if input_data is None or (isinstance(input_data, str) and not input_data.strip()):
            print(f"\033[91m[{debug_prefix}JSON解析错误] 输入为空\033[0m")
            return {}
            
        # 如果不是字符串，尝试转换为字符串
        if not isinstance(input_data, str):
            try:
                input_data = str(input_data)
            except Exception as e:
                print(f"\033[91m[{debug_prefix}无法转换为字符串] {str(e)}\033[0m")
                return {}
                
        # 尝试直接解析
        try:
            return JsonUtils.parse_json(input_data)
        except ValueError as e:
            print(f"\033[91m[{debug_prefix}JSON解析错误] {str(e)}\033[0m")
            
            # 尝试从文本中提取JSON
            json_str = JsonUtils.extract_json_from_text(input_data)
            if json_str:
                try:
                    result = JsonUtils.parse_json(json_str, fix_format=True)
                    return result
                except Exception as e2:
                    print(f"\033[91m[{debug_prefix}JSON修复后依然出错] {str(e2)}\033[0m")
            else:
                print(f"\033[91m[{debug_prefix}无法从文本中提取JSON] {input_data[:200]}...\033[0m" if len(input_data) > 200 else f"\033[91m[{debug_prefix}无法从文本中提取JSON] {input_data}\033[0m")
        
        # 如果所有解析尝试都失败，返回空字典
        return {} 