import httpx
from typing import Dict, Any
from fastapi import HTTPException, status

from app.schemas.test_result import MLPredictionRequest, MLPredictionResponse, QuestionResponses
from app.config import settings


class MLService:
    """Servicio para comunicarse con el modelo ML externo"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Inicializa el servicio ML.
        
        Args:
            base_url: URL del servicio ML (ej: "http://ml-api.example.com")
            timeout: Tiempo máximo de espera en segundos
        """
        # TODO: Agregar ML_SERVICE_URL a settings.py cuando tengas la URL
        self.base_url = base_url or getattr(settings, 'ML_SERVICE_URL', 'https://burnoutml.onrender.com')
        self.timeout = timeout
        self.prediction_endpoint = f"{self.base_url}/predict"
    
    async def predict(self, data: MLPredictionRequest) -> MLPredictionResponse:
        """
        Envía datos al servicio ML y obtiene la predicción.
        
        Args:
            data: Datos del test en formato esperado por el ML
        
        Returns:
            Respuesta del ML con predicción, probabilidad y versión del modelo
        
        Raises:
            HTTPException: Si hay error en la comunicación o el ML falla
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.prediction_endpoint,
                    json=data.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                # Verificar respuesta exitosa
                response.raise_for_status()
                
                # Parsear respuesta
                ml_response = response.json()
                
                print(self.base_url)
                
                # Validar estructura de respuesta
                return MLPredictionResponse(**ml_response)
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="El servicio de predicción no respondió a tiempo"
            )
        
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error del servicio de predicción: {e.response.status_code}"
            )
        
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar al servicio de predicción: {str(e)}"
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado en la predicción: {str(e)}"
            )
    
    def build_prediction_request(self, test_data: Dict[str, Any], responses: Dict[str, str]) -> MLPredictionRequest:
        
        """
        Construye el objeto de request para el ML a partir de datos del test.
        
        Args:
            test_data: Datos demográficos del test (ciclo, genero, facultad, practicasprepro)
            responses: Diccionario con las respuestas {question_key: answer_value}
                       ej: {"pregunta1": "A menudo", "pregunta2": "Rara vez", ...}
        
        Returns:
            MLPredictionRequest listo para enviar al servicio ML
        """
        
        question_data = {
            "ciclo":test_data["ciclo"],
            "genero":test_data["genero"],
            "facultad":test_data["facultad"],
            "practicasprepro":test_data["practicasprepro"],
            "pregunta1":responses.get("pregunta1", ""),
            "pregunta2":responses.get("pregunta2", ""),
            "pregunta3":responses.get("pregunta3", ""),
            "pregunta4":responses.get("pregunta4", ""),
            "pregunta5":responses.get("pregunta5", ""),
            "pregunta6":responses.get("pregunta6", ""),
            "pregunta7":responses.get("pregunta7", ""),
            "pregunta8":responses.get("pregunta8", ""),
            "pregunta9":responses.get("pregunta9", ""),
            "pregunta10":responses.get("pregunta10", ""),
            "pregunta11":responses.get("pregunta11", ""),
            "pregunta12":responses.get("pregunta12", ""),
            "pregunta13":responses.get("pregunta13", ""),
            "pregunta14":responses.get("pregunta14", ""),
            "pregunta15":responses.get("pregunta15", ""),
            "pregunta16":responses.get("pregunta16", ""),
            "pregunta17":responses.get("pregunta17", ""),
            "pregunta18":responses.get("pregunta18", ""),
            "pregunta19":responses.get("pregunta19", "")
        }
        
        question_responses_obj = QuestionResponses(**question_data)
        
        return MLPredictionRequest(
            respuestas=question_responses_obj
        )


# Instancia global del servicio
ml_service = MLService()