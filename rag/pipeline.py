from rag import llm,rag
import json

def outline_agent(topic: str) -> str:
    """题目 → 大纲文本，内部拼 prompt 调 LLM()"""
    prompt=f"""请为教材《{topic}》写目录，注意简洁明了，只写最主要的概念。不要在目录前后输出任何无关的内容。格式为（ xxx 表示占位符，实际内容由你填充，结构也可自行参照规律按需增加或减少）：
        第1章 xxx
            1.1 xxx
                1.1.1 xxx
                1.1.2 xxx
            1.2 xxx
                1.2.1 xxx
                1.2.2 xxx
        第2章 xxx
            2.1 xxx
                2.1.1 xxx
                2.1.2 xxx
            2.2 xxx 
                2.2.1 xxx
                2.2.2 xxx
        第3章 xxx
            
    """
    return llm.LLM(prompt,"",[])


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
    size=3;
    draft_chunks=[]
    for i in range(0,len(draft),size):
        if (i+size)<=len(draft):
            draft_chunks.append(draft[i:i+size])
                
        else :draft_chunks.append(draft[i:len(draft)])

    corpus_chunks=[];found=0;
    for j in range(0,len(corpus),size):
        if (j+size)<=len(corpus):
            corpus_chunks.append(corpus[j:j+size])
        
        else: corpus_chunks.append(corpus[j:len(corpus)])

    corpus_set = set(corpus_chunks)
    for i in draft_chunks:
        if i in corpus_set:
            found+=1;

    if len(draft_chunks)==0 :
        raise ValueError(r"稿子数组长度为0，检查D:\Learning\pub_of_agent\rag\pipeline.py")

    re=found/len(draft_chunks)
    return re


def generate_outline(topic:str)->str:
    outline=outline_agent(topic)
    return outline


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
    outline=generate_outline("线性代数")
    draft=generate_section("线性代数在监督学习中的作用")
    print(outline,draft)
