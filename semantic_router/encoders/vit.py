from typing import Any, List, Optional

from PIL import Image
from PIL.Image import Image as _Image
from pydantic.v1 import PrivateAttr

from semantic_router.encoders import BaseEncoder


class VitEncoder(BaseEncoder):
    name: str = "google/vit-base-patch16-224"
    type: str = "huggingface"
    score_threshold: float = 0.5
    processor_kwargs: dict = {}
    model_kwargs: dict = {}
    device: Optional[str] = None
    _processor: Any = PrivateAttr()
    _model: Any = PrivateAttr()
    _torch: Any = PrivateAttr()
    _T: Any = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._processor, self._model = self._initialize_hf_model()

    def _initialize_hf_model(self):
        try:
            from transformers import ViTImageProcessor, ViTModel
        except ImportError:
            raise ImportError(
                "Please install transformers to use HuggingFaceEncoder. "
                "You can install it with: "
                "`pip install semantic-router[local]`"
            )

        try:
            import torch
            import torchvision.transforms as T
        except ImportError:
            raise ImportError(
                "Please install Pytorch to use HuggingFaceEncoder. "
                "You can install it with: "
                "`pip install semantic-router[local]`"
            )

        self._torch = torch
        self._T = T

        processor = ViTImageProcessor.from_pretrained(
            self.name, **self.processor_kwargs
        )

        model = ViTModel.from_pretrained(self.name, **self.model_kwargs)

        if self.device:
            model.to(self.device)

        else:
            device = "cuda" if self._torch.cuda.is_available() else "cpu"
            model.to(device)
            self.device = device

        return processor, model

    def _process_images(self, images: List[_Image]):
        rgb_images = [self._ensure_rgb(img) for img in images]
        processed_images = self._processor(images=rgb_images, return_tensors="pt")
        processed_images = processed_images.to(self.device)
        return processed_images

    def _ensure_rgb(self, img: _Image):
        rgbimg = Image.new("RGB", img.size)
        rgbimg.paste(img)
        return rgbimg

    def __call__(
        self,
        imgs: List[_Image],
        batch_size: int = 32,
    ) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(imgs), batch_size):
            batch_imgs = imgs[i : i + batch_size]
            batch_imgs_transform = self._process_images(batch_imgs)
            with self._torch.no_grad():
                embeddings = (
                    self._model(**batch_imgs_transform)
                    .last_hidden_state[:, 0]
                    .cpu()
                    .tolist()
                )
            all_embeddings.extend(embeddings)
        return all_embeddings
