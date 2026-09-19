from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

knowledge_base = Path("KnowledgeBase")

# PDF LOAD
pdf_files = list(knowledge_base.rglob("*.pdf"))

all_documents = []
for pdf in pdf_files:
    loader = PyPDFLoader(pdf)
    documents = loader.load()
    
    # print(pdf.name)
    # print(pdf.stem)
    # print(pdf.parent.name)  
    
    # Get the name of the parent folder.
    # Example:
    # Kerala.pdf → "national"
    # Japan.pdf → "international"
    # Budget_Guidelines.pdf → "KnowledgeBase"
    region = pdf.parent.name
    
    # Get the filename without ".pdf".
    # Example: Kerala.pdf → "Kerala"
    destination = pdf.stem
    
    # Check whether this PDF belongs to a specific national or international destination.
    if region == "national" or region == "international":
        for document in documents:
            document.metadata["region"] = region # Store whether the destination is national or international.
            document.metadata["destination"] = destination # Store the destination name.
            document.metadata["document_type"] = "destination_guide"

    
    # If the PDF wasn't inside national/international,it must be one of our general knowledge PDFs.
    else:  
        for document in documents:
            document.metadata["region"] = "general"
            document.metadata["destination"] = None # These documents don't represent a destination, so we don't assign one.
            document.metadata["document_type"] = "general_guidelines"

        
    all_documents.extend(documents)
    
# print(all_documents[0].page_content[:1000])
# print(all_documents[0].metadata)
# print(all_documents[50].metadata)

#### CHUNKING ####

text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)

chunks = text_splitter.split_documents(all_documents)

# print(len(chunks))

# print("\n--- FIRST CHUNK ---")
# print(chunks[0].page_content)

# print("\n--- METADATA ---")
# print(chunks[0].metadata)


#####  EMBEDDINGS  #####

