import base64
import io
import os

import modal
from fastapi import FastAPI
from pydantic import BaseModel

# ─── Image: Gemma 4 with transformers + FastAPI ──────────────────────────────

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "transformers>=4.50.0",
        "torch==2.5.1",
        "accelerate",
        "hf-transfer",
        "fastapi",
        "pillow",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("ai-lorekeeper-gemma")
web_app = FastAPI()


class ChatRequest(BaseModel):
    messages: list[dict]
    max_tokens: int = 4096
    temperature: float = 0.7


class DescribeImageRequest(BaseModel):
    image_base64: str
    prompt: str = (
        "Describe what you see in this image in detail. Include any text you can read."
    )


# ─── Model Class ──────────────────────────────────────────────────────────────


@app.cls(
    image=image,
    gpu="A10G",
    scaledown_window=300,
    secrets=[modal.Secret.from_dotenv("../backend/.env")],
)
class LorekeeperEngine:
    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        model_id = os.environ.get("GEMMA_MODEL_ID", "google/gemma-4-E4B-it")
        print(f"Loading {model_id}...")
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        print("Model loaded!")

    @modal.method()
    def generate(self, messages, max_tokens, temperature):
        prompt = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
        )
        text = self.processor.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        )
        return text

    @modal.method()
    def describe_image(self, image_base64: str, prompt: str):
        """Analyze an image and return a text description."""
        import torch
        from PIL import Image as PilImage

        # Decode base64 to image
        image_data = base64.b64decode(image_base64)
        pil_image = PilImage.open(io.BytesIO(image_data))

        # Use processor for multimodal input
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        prompt_text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=prompt_text, images=pil_image, return_tensors="pt"
        ).to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.3,
            do_sample=True,
        )
        text = self.processor.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        )
        return text.strip()


# ─── API Routes ───────────────────────────────────────────────────────────────


@app.function(image=image)
@modal.asgi_app()
def serve():
    engine = LorekeeperEngine()

    @web_app.post("/v1/chat/completions")
    async def chat(request: ChatRequest):
        text = await engine.generate.remote.aio(
            request.messages, request.max_tokens, request.temperature
        )
        return {"choices": [{"message": {"content": text, "role": "assistant"}}]}

    @web_app.post("/v1/describe-image")
    async def describe_image(request: DescribeImageRequest):
        description = await engine.describe_image.remote.aio(
            request.image_base64, request.prompt
        )
        return {"description": description}

    @web_app.get("/v1/models")
    async def list_models():
        return {
            "data": [{"id": os.environ.get("GEMMA_MODEL_ID", "google/gemma-4-E4B-it")}]
        }

    @web_app.get("/health")
    async def health():
        return {"status": "ok"}

    return web_app
