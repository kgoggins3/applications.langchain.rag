import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from ragas import Dataset, experiment
from ragas.llms import llm_factory
from ragas.metrics import DiscreteMetric
from openai import AzureOpenAI

load_dotenv()

# Add the current directory to the path so we can import rag module when run as a script
sys.path.insert(0, str(Path(__file__).parent))
from rag import default_rag_client

#azure client initialization
azure_endpoint = os.getenv("AZURE_ENDPOINT")
azure_api_key = os.getenv("OPEN_AI_AZURE_KEY")
deployment_name = "rag-pipeline-openai"

openai_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
    azure_deployment="gpt-4o"
)

rag_client = default_rag_client(llm_client=openai_client)
llm = llm_factory("gpt-4o", client=openai_client)

#function that came with the ragas evals to create a sample dataset
def load_dataset():
    dataset = Dataset(
        name="test_dataset",
        backend="local/csv",
        root_dir=".",
    )

    data_samples = [
        {
            "question": "What is ragas 0.3",
            "grading_notes": "- experimentation as the central pillar - provides abstraction for datasets, experiments and metrics - supports evals for RAG, LLM workflows and Agents",
        },
        {
            "question": "how are experiment results stored in ragas 0.3?",
            "grading_notes": "- configured using different backends like local, gdrive, etc - stored under experiments/ folder in the backend storage",
        },
        {
            "question": "What metrics are supported in ragas 0.3?",
            "grading_notes": "- provides abstraction for discrete, numerical and ranking metrics",
        },
    ]

    for sample in data_samples:
        row = {"question": sample["question"], "grading_notes": sample["grading_notes"]}
        dataset.append(row)

    # make sure to save it
    dataset.save()
    return dataset

#function to load dataset from the generated q/a pairs to send for rag evaluation
def load_dataset_from_qa(qa_results):
    """
    qa_results = [
        {
            "document_name": "a.docx",
            "qa_pairs": [
                {"question": "...", "answer": "..."},
                ...
            ]
        }
    ]
    """
    dataset = Dataset(
        name="generated_qa_dataset",
        backend="local/csv",
        root_dir=str(Path(__file__).parent),
    )

    import json

    for doc in qa_results:
        qa_json = json.loads(doc["qa_pairs"])
        for pair in qa_json["qa_pairs"]:
            dataset.append({
                "question": pair["question"],
                "grading_notes": pair["answer"], # used as reference
            })

    dataset.save()
    return dataset

#correctness definition for rag evaluation
my_metric = DiscreteMetric(
    name="correctness",
    prompt="Check if the response contains points mentioned from the grading notes and return 'pass' or 'fail'.\nResponse: {response} Grading Notes: {grading_notes}",
    allowed_values=["pass", "fail"],
)

#experiment definition for rag evaluation
def create_run_experiment(rag_client, llm_instance, metric_instance):
    @experiment()
    async def run_experiment(row):
        response = rag_client.query(row["question"])

        score = metric_instance.score(
            llm=llm_instance,
            response=response.get("answer", " "),
            grading_notes=row["grading_notes"],
        )

        return {
            **row,
            "response": response.get("answer", ""),
            "score": score.value,
            "log_file": response.get("logs", " "),
        }
    return run_experiment

#function to run the rag evaluation from the generated q/a pairs and return the results as a pandas dataframe - easiest for streamlit digestion 
async def run_evaluation_from_qa(qa_results, documents=None):
    dataset = load_dataset_from_qa(qa_results)

    if documents:
        from rag import default_rag_client
        # Use same Azure client as page.py
        rag_client_instance = default_rag_client(llm_client=openai_client)
        rag_client_instance.set_documents(documents)
    else:
        from rag_eval.evals import rag_client
        rag_client_instance = rag_client

    run_experiment_instance = create_run_experiment(
        rag_client_instance, llm, my_metric
    )

    experiment_results = await run_experiment_instance.arun(dataset)
    experiment_results.save()
    return experiment_results.to_pandas()


#main function that came from the installation of ragas evals to run the experiment
async def main():
    dataset = load_dataset()
    print("dataset loaded successfully", dataset)
    experiment_results = await run_experiment.arun(dataset)
    print("Experiment completed successfully!")
    print("Experiment results:", experiment_results)

    # Save experiment results to CSV
    experiment_results.save()
    csv_path = Path(".") / "experiments" / f"{experiment_results.name}.csv"
    print(f"\nExperiment results saved to: {csv_path.resolve()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
