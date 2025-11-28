"""
Qwen LLM Manager

Qwen model을 사용하여 텍스트 생성 및 질의 응답을 처리합니다.
싱글톤 패턴으로 모델을 캐싱하여 속도를 개선합니다.
"""
from typing import List, Optional, Dict, Any
import logging
import threading
import torch
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from src.settings import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    모델 로더 싱글톤
    
    HuggingFace 모델을 한 번만 로드하여 메모리에 캐싱하고 재사용합니다.
    """
    _instance: Optional['ModelLoader'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelLoader, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """초기화 (한 번만 실행)"""
        if self._initialized:
            return
        
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = None
        self._initialized = True
        logger.info("ModelLoader singleton instance created")
    
    def load_model(
        self,
        model_name: str = "Qwen/Qwen2.5-4B-Instruct",
        device: Optional[str] = None,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
        trust_remote_code: bool = True
    ):
        """
        HuggingFace 모델 로드 및 캐싱
        
        Args:
            model_name: HuggingFace 모델 이름 (기본값: Qwen2.5-4B-Instruct)
            device: 사용할 디바이스 ("cuda", "cpu", None=자동)
            load_in_8bit: 8비트 양자화 사용 여부
            load_in_4bit: 4비트 양자화 사용 여부
            trust_remote_code: 원격 코드 신뢰 여부
        """
        if self.model is not None and self.model_name == model_name:
            logger.info("Model already loaded: " + model_name)
            return
        
        logger.info("Starting model loading: " + model_name)
        
        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info("Using device: " + self.device)
        
        # CPU 환경에서는 양자화를 사용할 수 없음 (bitsandbytes는 CUDA 필요)
        if self.device == "cpu" and (load_in_4bit or load_in_8bit):
            logger.warning("Quantization is not supported on CPU. Disabling quantization.")
            load_in_4bit = False
            load_in_8bit = False
        
        try:
            # 토크나이저 로드
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=trust_remote_code,
                cache_dir=settings.cache_dir
            )
            
            # 모델 로드 설정
            model_kwargs = {
                "trust_remote_code": trust_remote_code,
                "cache_dir": settings.cache_dir
            }
            
            # 양자화 설정 (CUDA 환경에서만)
            if load_in_4bit and self.device != "cpu":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
                model_kwargs["quantization_config"] = quantization_config
                logger.info("Using 4-bit quantization")
            elif load_in_8bit and self.device != "cpu":
                model_kwargs["load_in_8bit"] = True
                logger.info("Using 8-bit quantization")
            
            # 모델 로드 (Qwen3-VL 등 Vision-Language 모델 지원)
            logger.info("Loading model... (this may take some time)")
            
            # 모델 타입 자동 감지: Qwen3-VL은 Vision-Language 모델이므로 AutoModel 사용
            # trust_remote_code=True로 모델 자체의 코드를 사용하여 올바른 클래스 자동 선택
            try:
                # 먼저 AutoModelForCausalLM 시도 (일반 텍스트 모델)
                if "qwen3-vl" not in model_name.lower() and "vl" not in model_name.lower():
                    logger.info("Using AutoModelForCausalLM for text-only model")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        **model_kwargs
                    )
                else:
                    # Vision-Language 모델은 AutoModel 사용 (trust_remote_code로 자동 클래스 선택)
                    logger.info("Detected Vision-Language model, using AutoModel with trust_remote_code")
                    self.model = AutoModel.from_pretrained(
                        model_name,
                        **model_kwargs
                    )
            except Exception as e:
                # AutoModelForCausalLM 실패 시 AutoModel로 재시도
                if "AutoModelForCausalLM" in str(e) or "configuration" in str(e).lower():
                    logger.warning("AutoModelForCausalLM failed, trying AutoModel: " + str(e))
                    self.model = AutoModel.from_pretrained(
                        model_name,
                        **model_kwargs
                    )
                else:
                    raise
            
            # 디바이스로 이동 (양자화 사용 시 자동으로 처리됨)
            if not load_in_8bit and not load_in_4bit:
                self.model = self.model.to(self.device)
            
            self.model.eval()  # 평가 모드로 설정
            self.model_name = model_name
            
            logger.info("Model loading completed: " + model_name)
            
        except Exception as e:
            logger.error("Model loading failed: " + str(e))
            raise
    
    def get_model(self):
        """로드된 모델 반환"""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self.model
    
    def get_tokenizer(self):
        """로드된 토크나이저 반환"""
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer not loaded. Call load_model() first.")
        return self.tokenizer
    
    def is_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self.model is not None and self.tokenizer is not None
    
    def clear_cache(self):
        """모델 캐시 정리 (메모리 해제)"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.model_name = None
        
        # GPU 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model cache cleared")


# 싱글톤 인스턴스 접근 함수
def get_model_loader() -> ModelLoader:
    """ModelLoader 싱글톤 인스턴스 반환"""
    return ModelLoader()


class QwenManager:
    """
    Qwen LLM 모델 관리자
    
    싱글톤 패턴의 ModelLoader를 통해 HuggingFace Qwen 모델을 사용합니다.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        load_in_8bit: Optional[bool] = None,
        load_in_4bit: Optional[bool] = None,
        **kwargs
    ):
        """
        Args:
            model_name: HuggingFace 모델 이름 (기본값: 설정값)
            device: 사용할 디바이스 ("cuda", "cpu", None=설정값)
            load_in_8bit: 8비트 양자화 사용 여부
            load_in_4bit: 4비트 양자화 사용 여부
            **kwargs: 추가 설정
        """
        self.model_name = model_name or settings.llm_model_name
        self.device = device or (settings.llm_device if settings.llm_device != "auto" else None)
        self.load_in_8bit = load_in_8bit if load_in_8bit is not None else settings.llm_load_in_8bit
        self.load_in_4bit = load_in_4bit if load_in_4bit is not None else settings.llm_load_in_4bit
        self.config = kwargs
        
        # 싱글톤 모델 로더 가져오기
        self.model_loader = get_model_loader()
        
        logger.info("Qwen Manager initialized with model: " + self.model_name)
    
    def initialize(self):
        """LLM 모델 초기화 (싱글톤에서 로드)"""
        if not self.model_loader.is_loaded():
            logger.info("Starting model loading: " + self.model_name)
            self.model_loader.load_model(
                model_name=self.model_name,
                device=self.device,
                load_in_8bit=self.load_in_8bit,
                load_in_4bit=self.load_in_4bit,
                trust_remote_code=settings.llm_trust_remote_code
            )
        else:
            logger.info("Model already loaded (using singleton cache)")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,  # 기본값을 500으로 줄임 (반복 방지)
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 생성 온도
            top_p: nucleus sampling 파라미터
            **kwargs: 추가 파라미터
            
        Returns:
            생성된 텍스트
        """
        # 모델이 로드되지 않았으면 초기화
        if not self.model_loader.is_loaded():
            self.initialize()
        
        model = self.model_loader.get_model()
        tokenizer = self.model_loader.get_tokenizer()
        
        if model is None:
            raise RuntimeError("Model is not loaded")
        if tokenizer is None:
            raise RuntimeError("Tokenizer is not loaded")
        
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        prompt_length = len(prompt)
        logger.info("LLM text generation requested with prompt length: " + str(prompt_length))
        
        try:
            # 프롬프트 토크나이징
            inputs = tokenizer(prompt, return_tensors="pt")
            
            # 디바이스로 이동
            device = self.model_loader.device
            if device and not self.load_in_8bit and not self.load_in_4bit:
                inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 텍스트 생성
            # Qwen3-VL 등 Vision-Language 모델도 generate 메서드를 지원하는지 확인
            with torch.no_grad():
                try:
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        do_sample=temperature > 0,
                        pad_token_id=tokenizer.eos_token_id if hasattr(tokenizer, 'eos_token_id') else None,
                        repetition_penalty=1.2,  # 반복 방지
                        no_repeat_ngram_size=3,  # 3-gram 반복 방지
                        **kwargs
                    )
                except AttributeError as e:
                    # generate 메서드가 없는 경우 (일부 Vision-Language 모델)
                    error_msg = "Model does not support generate method. Qwen3-VL may require image inputs. Error: " + str(e)
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
            
            # outputs 검증
            if outputs is None or len(outputs) == 0:
                raise RuntimeError("Model generation returned empty output")
            
            # 디코딩
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 프롬프트 제거 (생성된 부분만 반환)
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            text_length = len(generated_text)
            logger.info("Text generation completed with length: " + str(text_length))
            return generated_text
            
        except Exception as e:
            logger.error("Text generation failed: " + str(e))
            raise
    
    async def generate_with_context(
        self,
        query: str,
        contexts: List[str],
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,  # 기본값을 500으로 설정
        **kwargs
    ) -> str:
        """
        컨텍스트를 포함한 텍스트 생성 (RAG용)
        
        Args:
            query: 사용자 질문
            contexts: 관련 컨텍스트 리스트
            system_prompt: 시스템 프롬프트
            **kwargs: 추가 파라미터
            
        Returns:
            생성된 답변
            
        Raises:
            ValueError: query나 contexts가 비어있는 경우
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not contexts:
            raise ValueError("Contexts cannot be empty")
        
        # 유효한 컨텍스트만 필터링
        valid_contexts = [ctx for ctx in contexts if ctx and ctx.strip()]
        if not valid_contexts:
            raise ValueError("All contexts are empty")
        
        # 컨텍스트 결합
        combined_context = "\n\n".join(valid_contexts)
        
        # 프롬프트 구성 (더 구조화된 형식)
        if system_prompt:
            prompt = system_prompt + "\n\n"
        else:
            prompt = "다음 문서를 참고하여 질문에 답변해주세요. 문서 내용을 꼼꼼히 읽고 분석하세요. 문서에 없는 내용은 추측하지 마세요.\n\n"
        
        prompt = prompt + "=== 참고 문서 내용 (표 형식 데이터 포함) ===\n" + combined_context + "\n==========================================\n\n"
        prompt = prompt + "사용자 질문: " + query + "\n\n"
        prompt = prompt + "**중요**: 문서에 나온 항목, 구성 요소, 용어를 확인하고 질문에 답변하세요. 표 형식 데이터도 포함됩니다.\n\n"
        prompt = prompt + "답변:"
        
        return await self.generate(prompt, **kwargs)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        채팅 형식의 대화 생성
        
        Args:
            messages: 메시지 리스트 [{"role": "user", "content": "..."}]
            max_tokens: 최대 토큰 수
            temperature: 생성 온도
            **kwargs: 추가 파라미터
            
        Returns:
            생성된 응답
        """
        # 모델이 로드되지 않았으면 초기화
        if not self.model_loader.is_loaded():
            self.initialize()
        
        tokenizer = self.model_loader.get_tokenizer()
        
        # 메시지를 프롬프트로 변환 (Qwen 형식)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        messages_count = len(messages)
        logger.info("LLM chat requested with messages count: " + str(messages_count))
        
        # generate 메서드 사용
        return await self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
