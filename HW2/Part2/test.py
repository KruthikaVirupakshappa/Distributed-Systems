from state import initialize_state
from workflow import build_workflow


def test_workflow_stream():

    app = build_workflow()
    
    title = "Build and run docker Image"
    content = """Docker Image is a read-only template to build containers. An image holds all 
    the information needed to bootstrap a container, including what processes 
    to run and the configuration data. Every image starts from a base image, 
    and a template is created by using the instructions that are stored in the 
    DockerFile. For each instruction, a new layer is created on the image. 
    Running the container originates from the image we created in the previous 
    step. When a container is launched, a read-write layer is added to the top of the 
    image. After appropriate network and IP address allocation, the desired 
    application can now be run inside the container."""
    
    initial_state = initialize_state(
        title=title,
        content=content,
        email="test@example.com",
        strict=True,
        task="Extract tags and summary from content"
    )
    
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTION")
    print("=" * 80)
    print(f"Title: {title}\n")
    
    try:
        current_turn = 0
        
        for output in app.stream(initial_state):
            node_name = list(output.keys())[0]
            node_state = output[node_name]
            
            # Get turn count from state (supervisor always has it)
            if node_name == "supervisor":
                current_turn = node_state.get('turn_count', 0)
            
            has_issues = node_state.get('reviewer_has_issues', None)
            proposal = node_state.get("planner_proposal", {})
            feedback = node_state.get("reviewer_feedback", {})
            
            print(f"\n--- Turn {current_turn}: {node_name.upper()} ---")
            
            if node_name == "supervisor":
                print(f"  (Turn count: {current_turn})")
            
            elif node_name == "planner":
                tags = proposal.get('tags', [])
                summary = proposal.get('summary', '')
                print(f"  Tags: {tags}")
                print(f"  Summary: {summary}")
            
            elif node_name == "reviewer":
                tags = feedback.get('tags', [])
                summary = feedback.get('summary', '')
                notes = feedback.get('review_notes', [])
                print(f"  Tags: {tags}")
                print(f"  Summary: {summary}")
                print(f"  Has issues: {has_issues}")
                if notes:
                    print(f"  Review notes: {notes}")
        
        print(f"\n" + "=" * 80)
        print(f"WORKFLOW COMPLETED")
        print(f"=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_workflow_stream()

