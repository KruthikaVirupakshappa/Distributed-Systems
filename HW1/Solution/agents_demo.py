import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

schema = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3
        },
        "summary": {"type": "string", "minLength": 80, "maxLength": 200}
    },
    "required": ["tags", "summary"],
    "additionalProperties": False
}


def call_ollama():
    try:
        llm = ChatOllama(
            model="smollm:1.7b",
            temperature=0.7,
            format=schema,
            num_predict=256
        )
        return llm
    except Exception as e:
        return f"Error: {str(e)}"

#Agent 1: Planner 
def planner_agent(title, content):
    """
    Planner Agent: Takes the input of blog's title and it's content to give the
    desired response.
    """
    prompt = f"""You are a SUMMARIZATION EXPERT. Analyze the following text and provide exactly:
        1. Three relevant tags (1-3 words each)
        2. A concise summary of 20-25 words that captures the main idea

        Strict Rules:
        Generate a NEW summary in your own words. Do not copy sentences from the text.
        Focus on the core concept and purpose.

        TITLE: {title}
        TEXT: {content}

        Return ONLY valid JSON with "tags" array and "summary" string."""
    llm = call_ollama()
    resp = llm.invoke([HumanMessage(content=prompt)])
    data = json.loads(resp.content)

    tags = data["tags"]    
    summary = data["summary"] 
    return tags, summary

def reviewer_agent(title, content, tags, summary):
    prompt = f"""You are a review agent.

    Your task:
    - Validate the provided tags and summary
    - Correct them ONLY if they violate the rules
    - If they are already correct, return them unchanged

    Rules:
    - tags: exactly 3 items, each 1-3 words, relevant to the text
    - summary: exactly 1 sentence, maximum 25 words, abstractive
    - Do NOT invent placeholder values
    - Do NOT return example text
    - Use the actual content to decide

    Return ONLY valid JSON with keys:
    - tags
    - summary

    TITLE:
    {title}

    TEXT:
    {content}

    CURRENT TAGS:
    {tags}

    CURRENT SUMMARY:
    {summary}
    """


    llm = call_ollama()
    resp = llm.invoke([HumanMessage(content=prompt)])
    data = json.loads(resp.content)

    tags = data["tags"]    
    summary = data["summary"] 
    return tags, summary

def finalization_step(tags, summary):
    """
    Finalization Step: validation and strict JSON output.
    """

    try:
        tags = tags[:3]
        while len(tags) < 3:
            tags.append("fill")

        if not isinstance(summary, str):
            summary = ""
        summary = summary.strip()
        words = summary.split()
        if len(words) > 25:
            summary = " ".join(words[:25]).rstrip(".") + "."
        if not summary:
            raise ValueError("Could not find valid summary")

        return json.dumps(
            {"tags": tags, "summary": summary},
        )

    except Exception as e:
        return f"Error: {str(e)}"

def main():
    
    title = "Build and run docker Image"
    content = """Docker Image is a read-only template to build containers. An image holds all
                the information needed to bootstrap a container, including what processes
                to run and the configuration data. Every image starts from a base image,
                and a template is created by using the instructions that are stored in the
                DockerFile. For each instruction, a new layer is created on the image.
                •Running the container originates from the image we created in the previous
                step. When a container is launched, a read-write layer is added to the top of the
                image. After appropriate network and IP address allocation, the desired
                application can now be run inside the container."""
    
    print("="*60)
    print(f"Title: {title}")
    print(f"Content: {content}")
    print()

    #Planner Agent
    print("="*60)
    print("Output from the planner agent:\n")
    planner_result = planner_agent(title, content)
    print(f"TAGS: {planner_result[0]}\n")
    print(f"SUMMARY: {planner_result[1]}\n")
    print()

    # Reviewer Agent
    print("="*60)
    print("Output from the Reviewer agent:\n")
    reviewer_result = reviewer_agent(title, content, planner_result[0], planner_result[1])
    print(f"TAGS: {reviewer_result[0]}\n")
    print(f"SUMMARY: {reviewer_result[1]}\n")
    # print()

    # #Finalization Agent
    print("="*60)
    print("Result from the Finalizer step:\n")
    final_result = finalization_step(reviewer_result[0], reviewer_result[1])
    print(final_result)
    print()

if __name__ == "__main__":
    main()
