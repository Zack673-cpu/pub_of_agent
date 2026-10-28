import llm,rag
import json
import difflib
import uuid
from pathlib import Path


base_prompt="""不要在目录前后输出任何无关的内容。输出格式为 '章节->分节->小节'（ 'xxx' 表示占位符，实际内容由你填充）：
        第1章 xxx
            1 xxx
                1.1.1 xxx
                1.1.2 xxx
                1.1.3 xxx
                1.1.4 xxx
            2 xxx
                1.2.1 xxx
                1.2.2 xxx
                1.2.3 xxx
            3 xxx
                1.3.1 xxx
        第2章 xxx
            1 xxx
                2.1.1 xxx
                2.1.2 xxx
            2 xxx 
                2.2.1 xxx
                2.2.2 xxx
        第3章 xxx
            1 xxx
                3.1.1 xxx
            2 xxx
                3.2.1 xxx
                3.2.2 xxx
                3.2.3 xxx
                3.2.4 xxx
                3.2.5 xxx

        以上只是示例，其中章节、分节、小节都可以自由扩充或缩减，一一对应即可。比如增加第4章1、2、3、4及其小节、第5章及其分节，也可以缩减，比如第2章只有1分节及其小节。
        不允许出现章节下面没有分节或分节下面没有小节，比如第4章下连1分节都没有，或者只有第4章和1分节，没有下面的小节4.1.1。不允许编号不按顺序，比如第4章的1分节下面写成5.1.1或者5.2.1。
        """

def outline_agent(title: str, requirement: str) -> str:
    """题目 → 大纲文本，内部拼 prompt 调 LLM()"""
    if requirement=="":requirement='无'
    prompt=f"""请为教材《{title}》写目录，注意简洁明了，只写最主要的概念。{base_prompt}如果以下要求允许，可以根据参考资料额外追加内容。追加的内容如果涉及数字一律用中文数字，比如一二三，不允许用123。
        额外要求：{requirement}
    """
    return llm.LLM(prompt,"",[])

def parse_outline(text: str) -> list[dict]:
    """大纲文本 → 节树"""
# [
#   {"node_key": "…", "title": "随机事件和概率", "children": [
#       {"node_key": "…", "title": "随机事件", "children": [
#           {"node_key": "…", "title": "随机试验与样本空间", "children": []},
#       ]},
#   ]},
# ]
    stack = []
    # [(node,indent)]
    lines=text.splitlines()
    res_section=[]

    for line in lines:
        if not line.strip(): continue 
        node_key=uuid.uuid4().hex
        parts=line.split(maxsplit=1)  #按照空格切分 
        if len(parts)==2:
            _,sec=parts
        else :
            sec=parts[0]
        indent = len(line) - len(line.lstrip())   # 前导空白字符的个数
        
        
        node={'node_key':node_key,'title':sec,'children':[]}

        if not stack:
                res_section.append(node)
                stack.append((node,indent))
        else :
            while(stack[-1][1]>=indent):
                stack.pop()
                if not stack:
                    res_section.append(node)
                    stack.append((node,indent))
                    break
            if  stack[-1][1]<indent:
                stack[-1][0]['children'].append(node)
                stack.append((node,indent))

            
    return res_section    



def align_nodes(old_tree:list[dict]|None, new_tree:list[dict])->list[dict]:
    """新树旧树处理"""
    if old_tree is None:return new_tree
    else :
        _align_level(old_tree,new_tree)
        return new_tree

def _align_level(old_nodes:list[dict], new_nodes:list[dict])->None:
    """同一父节点下，两组兄弟节点提取标题，只有标题一样才修改新树的key(用旧的key)"""
    if old_nodes is None or new_nodes is None:return    
    old_titles=[]
    new_titles=[]
    for old in old_nodes:old_titles.append(old['title'])
    for new in new_nodes:new_titles.append(new['title'])
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher( None , old_titles,new_titles).get_opcodes():
        #difflib.SequenceMatcher后面两个参数只接收可迭代的，get_opcodes() 返回一个 列表 ，每项是 5 元组：(tag, i1, i2, j1, j2)
        # old_titles = ['随机事件和概率', '随机事件', '随机试验与样本空间']
        # new_titles = ['随机事件和概率', '随机事件的定义', '随机试验与样本空间', '样本空间']
        # 则返回：
        # [('equal',   0, 1, 0, 1),
        # ('replace', 1, 2, 1, 2),
        # ('equal',   2, 3, 2, 3),
        # ('insert',  3, 3, 3, 4)]

        
        if tag=='equal':
                for k in range(i2-i1):
                    new_nodes[j1+k]['node_key']=old_nodes[i1+k]['node_key']
                    _align_level(old_nodes[i1+k]['children'],new_nodes[j1+k]['children'])

    return


def revise_outline_agent(old_tree: list[dict], instruction: str) -> str:
    """旧节树 + 修订指令 → 新大纲文本（格式同 outline_agent 输出）"""

    prompt=f"""按照给出的要求修改已经有的目录。{base_prompt}除要求改动的地方，其余原样保留，不许自行扩写。
        目录开始：{_render_tree(old_tree,0)}目录结束。
        要求开始：{instruction}要求结束。
    """
    
    return llm.LLM(prompt,"",[])
    

def _render_tree(nodes: list[dict], depth: int) -> str:
   #`depth` ＝ 当前这一层是树里的第几层 （0＝章级，1＝分节，2＝小节）。要从这一层开始往下遍历。
    """节树 → 缩进文本：章级一行"第{n}章 {title}"，其余层只写 title，每层缩进 4 空格"""
    if nodes == [] or nodes is None:return ""
    res=""
    for n,node in enumerate(nodes):#enumerate()返回的是(下标，元素)
        if depth==0:
            res+=f"\n第{n+1}章 {node['title']}"
        else:
            res+=f"\n"+"    "*depth+f"{node["title"]}"
        res+=_render_tree(node["children"],depth+1)    
    return res

def summarize_agent(section: str, draft: str) -> str:
    """节标题 + 本节正文 → 约 150 字摘要卡（概念/定义/伏笔）"""
    prompt=f"""将以下正文压缩成不超过150字的摘要卡。卡的结构固定成三类槽位（概念/定义/伏笔），要求逐条列出，而不是写一段散文。保留主要信息，包含概念/定义/伏笔。不许为了凑字数加原文没有的内容。不许整段照抄原文，要的是概括。不要输出任何无关的东西。
        标题开始：{section} 标题结束
        正文开始：{draft} 正文结束
    """
    return llm.LLM(prompt, "", [])

def build_glossary(old_glossary: list[dict], section: str, card: str) -> list[dict]:
    """已有术语表 + 本节标题 + 本节摘要卡 → 合并后的完整术语表（旧表为准）"""
    form="[{\"term\": \"\", \"definition\": \"\"}]"
    prompt=f"""我会给你已有术语表 + 本节标题 + 本节摘要卡。只提取本章出现的、已有术语表里没有的新术语，不要重复已有术语，不要改写已有术语。没有新术语就输出空数组 []。不要输出任何无关的东西。输出格式如下（只是格式展示，真实要你填充内容）：
            `{form}`
            已有术语表：{old_glossary}
            本节标题：{section}
            本节摘要卡：{card}
    """
    for i in range(0,3):
        res=llm.LLM(prompt, "", [])
        try:
          return _merge_glossary(old_glossary, _parse_glossary(res), section)
        except ValueError:
            if i !=2:continue
            raise


def _merge_glossary(old_glossary: list[dict], new_items: list[dict], section: str) -> list[dict]:
    """旧表为准：旧条目原样保留，新术语只在表里没有同名时才追加（first_section 记本节）"""
    merged=list(old_glossary)
    seen={item["term"] for item in merged}
    for item in new_items:
        if item["term"] in seen:continue
        seen.add(item["term"])
        merged.append({"term":item["term"],"definition":item["definition"],"first_section":section})
    return merged


def _parse_glossary(text: str) -> list[dict]:
    """术语表文本 → [{"term": ..., "definition": ...}]"""
    _REQUIRED_KEYS = ("term", "definition")
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        r=json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"术语表不是合法 JSON: {e}") from e
    if not isinstance(r, list):
        raise ValueError(f"术语表应为 JSON 数组，实际是 {type(r).__name__}")
    for i, item in enumerate(r):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i} 条不是对象，实际是 {type(item).__name__}")
        missing = [k for k in _REQUIRED_KEYS if k not in item]
        if missing:
            raise ValueError(f"第 {i} 条缺少字段: {missing}")
    return r
    

def writer_agent(section: str, knowledge: list[str]) -> str:
    """大纲一节 + RAG 素材 → 正文初稿，内部调 LLM()"""
    prompt=f"""依据大纲：{section} 写一篇正文初稿，从参考素材里提取必要知识，组织好语言编写，条理清晰，详略得当。
        篇幅上限为1000字，篇幅下限为800字，不许整段重复前文。不许为了凑字数写一些无关内容。不要使用公式，尤其是数学符号，用普通中文写文章。
        直接输出初稿，不要在文章开头和结尾加任何无关内容，比如全文共648字这种。
    """
    return llm.LLM(prompt,knowledge,[])   


def review_agent(draft: str) -> str:
    """初稿 → 问题清单文本，内部调 LLM()"""
    prompt=f"这是初稿：{draft}初稿结束。仔细审查，确保没有语言错误，知识错误，如果有任何问题，写出问题分别有哪些。如果没有问题，只返回 ok"
    return llm.LLM(prompt,"",[])


def rewrite_agent(draft: str, issues: str) -> str:
    """初稿 + 问题清单 → 改写稿，内部调 LLM()"""
    prompt=f"这是初稿：{draft}初稿结束。这是问题清单：{issues}清单结束。根据问题清单，修改初稿，使其没有问题。"
    return llm.LLM(prompt,"",[])



def check_duplicate(draft: str, corpus: str) -> float:
    """稿子 + 比对文本 → 重复率，可用简单字符重叠算，不必调模型"""
    size=3
    draft_chunks=[]
    for i in range(0,len(draft),size):
        if (i+size)<=len(draft):
            draft_chunks.append(draft[i:i+size])
                
        else :draft_chunks.append(draft[i:len(draft)])

    corpus_chunks=[];found=0
    for j in range(0,len(corpus),size):
        if (j+size)<=len(corpus):
            corpus_chunks.append(corpus[j:j+size])
        
        else: corpus_chunks.append(corpus[j:len(corpus)])

    corpus_set = set(corpus_chunks)
    for i in draft_chunks:
        if i in corpus_set:
            found+=1

    if len(draft_chunks)==0 :
        raise ValueError(r"稿子数组长度为0，检查D:\Learning\pub_of_agent\rag\pipeline.py")

    re=found/len(draft_chunks)
    return re





def generate_section(section:str) -> str:
    """串联以上五步，管重写循环（审校有问题→降重→再审，最多 N 轮）"""
      
    with open(rag.restore_path,"r",encoding="utf-8") as f:
        text_vectors=f.read()

    text_vectors=json.loads(text_vectors)
    corpus=""
    for i in text_vectors:
        corpus+=i["text"]
    N=5
    
    o_vectors=rag.get_embedding(section)
    
    knowledge=rag.retrieve(o_vectors,text_vectors)
    #[(分数,文本)]
    
    draft=writer_agent(section,knowledge)

    for i in range(0,N):

        problem_list=review_agent(draft)
        if("ok" in problem_list):
            res=check_duplicate(draft,corpus)

            if res<0.1:return draft
            else :draft=rewrite_agent(draft,"重复率偏高，请改写降低与素材的重复")

        else:
            draft=rewrite_agent(draft,problem_list)

    return draft


if __name__=="__main__":
    text_path=Path(__file__).parent/'corpus'/'概率论与数理统计（第二版）_目录.md'
    # outline=outline_agent("大学本科范围的基础线性代数","写五章，每章要清晰明了，既要抽象简化方便理解，又要有专业推导经得起推敲")
    # # draft=generate_section("线性代数在监督学习中的作用")
    # print(outline)
    with open(text_path,'r',encoding='utf-8') as f:
        text=f.read()

    tree=parse_outline(text)
    print(align_nodes(None,tree))
    