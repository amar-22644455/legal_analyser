import os
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pickle
from PIL import Image
import pytesseract
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import CLIPProcessor, CLIPModel
import torch
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --------------------------
# Models
# --------------------------
# Text embedding (lightweight model for embeddings)
text_model = SentenceTransformer("all-MiniLM-L6-v2")

# BLIP model for image captions
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# CLIP model for image embeddings
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# --------------------------
# Functions
# --------------------------
def describe_image(image):
    """Generate a caption for an image using BLIP."""
    try:
        # Ensure image is PIL Image
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        
        inputs = blip_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            out = blip_model.generate(**inputs, max_length=50)
        
        # Decode the generated token IDs to text
        caption = blip_processor.tokenizer.decode(out[0], skip_special_tokens=True)
        return caption.strip() if caption else "No caption generated"
    except Exception as e:
        print(f"Warning: BLIP caption generation failed: {e}")
        return "Caption generation failed"

def get_image_embedding(image):
    """Generate CLIP embedding for an image."""
    try:
        # Ensure image is PIL Image
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        
        inputs = clip_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            image_emb = clip_model.get_image_features(**inputs)
        
        return image_emb.squeeze(0).cpu().numpy()  # convert to 1D numpy array
    except Exception as e:
        print(f"Warning: CLIP embedding generation failed: {e}")
        return None

DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
EMBEDDINGS_DIR = os.path.join(PROJECT_ROOT, "embeddings")

def create_embeddings():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    # Master dictionary to hold all grouped data
    # Format: {"filename.pdf": {"chunks": [...], "metadata": [...], "embeddings": [...]}}
    document_data = {} 
    image_embeddings_data = {} # Separate dictionary for CLIP embeddings

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=80
    )

    for file in os.listdir(DOCS_DIR):
        path = os.path.join(DOCS_DIR, file)
        
        # Temporary lists for the CURRENT file only
        current_file_chunks = []
        current_file_metadata = []
        
        # --------------------------
        # 📄 PDF Processing
        # --------------------------
        if file.lower().endswith(".pdf"):
            try:
                pdf = fitz.open(path)
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    page_text = page.get_text().strip()

                    if not page_text:
                        continue

                    page_chunks = splitter.split_text(page_text)
                    for chunk_index, chunk in enumerate(page_chunks):
                        current_file_chunks.append(chunk)
                        current_file_metadata.append({
                            "type": "pdf",
                            "page": page_num + 1,
                            "chunk_index": chunk_index,
                            "total_pages": len(pdf)
                        })
            except Exception as exc:
                print(f"Warning: could not process PDF '{path}': {exc}")

        # --------------------------
        # 📄 TXT Processing
        # --------------------------
        elif file.lower().endswith(".txt"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()

                if text:
                    txt_chunks = splitter.split_text(text)
                    for chunk_index, chunk in enumerate(txt_chunks):
                        current_file_chunks.append(chunk)
                        current_file_metadata.append({
                            "type": "txt",
                            "chunk_index": chunk_index
                        })
            except Exception as exc:
                print(f"Warning: could not process text file '{path}': {exc}")

        # --------------------------
        # 🖼️ Image Processing
        # --------------------------
        elif file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            try:
                image = Image.open(path)
                ocr_text = pytesseract.image_to_string(image).strip()
                caption = describe_image(image)

                combined_text = f"Caption: {caption}\nOCR Text: {ocr_text}" if ocr_text else f"Caption: {caption}"

                if combined_text.strip():
                    img_chunks = splitter.split_text(combined_text)
                    for chunk_index, chunk in enumerate(img_chunks):
                        current_file_chunks.append(chunk)
                        current_file_metadata.append({
                            "type": "image",
                            "chunk_index": chunk_index
                        })

                # CLIP embedding for whole image
                img_emb = get_image_embedding(image)
                if img_emb is not None:
                    image_embeddings_data[file] = img_emb

            except Exception as exc:
                print(f"Warning: could not process image '{path}': {exc}")

        # --------------------------
        # 🔢 Embed and Store the File's Data
        # --------------------------
        # If we successfully extracted text for THIS file, embed it and save it to the dictionary
        if current_file_chunks:
            print(f"Embedding {len(current_file_chunks)} chunks for {file}...")
            file_embeddings = text_model.encode(current_file_chunks, show_progress_bar=False)
            
            # Store everything neatly under the filename key
            document_data[file] = {
                "chunks": current_file_chunks,
                "metadata": current_file_metadata,
                "embeddings": file_embeddings
            }

    if not document_data:
        print("No document text found to embed across any files.")
        return False

    # --------------------------
    # 💾 Save the dictionaries
    # --------------------------
    with open(os.path.join(EMBEDDINGS_DIR, "document_data.pkl"), "wb") as f:
        pickle.dump(document_data, f)

    with open(os.path.join(EMBEDDINGS_DIR, "image_embeddings_data.pkl"), "wb") as f:
        pickle.dump(image_embeddings_data, f)

    print(f"Successfully processed and grouped {len(document_data.keys())} files.")
    return True