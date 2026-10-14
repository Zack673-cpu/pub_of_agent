import llm,rag
import json
import difflib
import uuid
from pathlib import Path
def outline_agent(title: str, requirement: str) -> str:
    """题目 → 大纲文本，内部拼 prompt 调 LLM()"""
    if requirement=="":requirement='无'
    prompt=f"""请为教材《{title}》写目录，注意简洁明了，只写最主要的概念。不要在目录前后输出任何无关的内容。格式为 '章节->分节->小节'（ 'xxx' 表示占位符，实际内容由你填充）：
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
        如果以下要求允许，可以根据参考资料额外追加内容。追加的内容一律用中文数字，比如一二三，不允许用123。
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
    """新树按标题序列对齐旧树，认回旧 node_key"""
    if old_tree is None:return new_tree

    # for i in old_tree:
    #     for j in i['children']:
    #         for k in j['children']:

        
    # difflib.SequenceMatcher( None , old_titles, new_titles).get_opcodes()

def _align_level(old_nodes:list[dict], new_nodes:list[dict])->None:
    """同一父节点下，两组兄弟节点按标题序列对齐"""
    ...



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

    print(parse_outline(text))
