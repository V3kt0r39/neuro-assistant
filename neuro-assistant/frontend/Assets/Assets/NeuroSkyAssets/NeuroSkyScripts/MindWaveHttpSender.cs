using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace MindWave
{
    public class MindWaveHttpSender : MonoBehaviour
    {
        [Header("HTTP settings")]
        public string endpointUrl = "http://stray-lid2.mooo.com:8000/api/analyze";

        [Tooltip("Как часто отправлять данные. 1.0 = раз в секунду, 0.5 = два раза в секунду")]
        public float sendInterval = 1.0f;

        [Tooltip("Отправлять запрос только если attention или meditation изменились")]
        public bool sendOnlyWhenValuesChanged = true;

        [Header("Debug")]
        public bool logRequestJson = true;
        public bool logResponseJson = true;

        private TGCConnectionController controller;

        private int attention;
        private int meditation;
        private int poorSignal;

        private int lastSentAttention = -1;
        private int lastSentMeditation = -1;

        private bool isSending = false;

        public string lastStatus = "";
        public string lastDetectedEmotion = "";
        public string lastAiRecommendation = "";
        public string lastSessionToken = "";
        public string lastDetectionMethod = "";
        public string lastRecommendationSource = "";
        public string lastServerError = "";

        [Serializable]
        private class AnalyzeRequest
        {
            public int concentration;
            public int relaxation;
            public int poor_signal;
        }

        [Serializable]
        private class AnalyzeResponse
        {
            public string status;
            public string detected_emotion;
            public string ai_recommendation;

            // Эти поля есть в твоём реальном ответе на скриншоте.
            public string session_token;
            public string detection_method;
            public string recommendation_source;

            // На случай если backend вернёт ошибку.
            public string detail;
            public string error;
            public string message;
        }

        private void Start()
        {
            controller = FindObjectOfType<TGCConnectionController>();

            if (controller == null)
            {
                Debug.LogError("MindWaveHttpSender: TGCConnectionController not found in scene.");
                return;
            }

            controller.UpdateAttentionEvent += OnUpdateAttention;
            controller.UpdateMeditationEvent += OnUpdateMeditation;
            controller.UpdatePoorSignalEvent += OnUpdatePoorSignal;

            StartCoroutine(SendLoop());
        }

        private void OnDestroy()
        {
            if (controller == null)
            {
                return;
            }

            controller.UpdateAttentionEvent -= OnUpdateAttention;
            controller.UpdateMeditationEvent -= OnUpdateMeditation;
            controller.UpdatePoorSignalEvent -= OnUpdatePoorSignal;
        }

        private void OnUpdateAttention(int value)
        {
            attention = value;
        }

        private void OnUpdateMeditation(int value)
        {
            meditation = value;
        }

        private void OnUpdatePoorSignal(int value)
        {
            poorSignal = value;
        }

        private IEnumerator SendLoop()
        {
            while (true)
            {
                yield return new WaitForSeconds(sendInterval);

                if (string.IsNullOrEmpty(endpointUrl))
                {
                    continue;
                }

                if (isSending)
                {
                    continue;
                }

                // Если сигнал плохой, можно не отправлять мусорные значения.
                // poorSignal = 0 — хороший сигнал.
                if (poorSignal >= 200)
                {
                    Debug.LogWarning("MindWaveHttpSender: poor signal, request skipped. poorSignal = " + poorSignal);
                    continue;
                }

                if (sendOnlyWhenValuesChanged)
                {
                    bool changed =
                        attention != lastSentAttention ||
                        meditation != lastSentMeditation;

                    if (!changed)
                    {
                        continue;
                    }
                }

                yield return StartCoroutine(SendAnalyzeRequest());
            }
        }

        private IEnumerator SendAnalyzeRequest()
        {
            isSending = true;

            AnalyzeRequest requestData = new AnalyzeRequest
            {
                // В backend attention отправляем как concentration.
                concentration = attention,

                // В backend meditation отправляем как relaxation.
                relaxation = meditation,

                poor_signal = poorSignal
            };

            string requestJson = JsonUtility.ToJson(requestData);

            if (logRequestJson)
            {
                Debug.Log("Unity -> Backend JSON: " + requestJson);
            }

            byte[] bodyRaw = Encoding.UTF8.GetBytes(requestJson);

            using (UnityWebRequest request = new UnityWebRequest(endpointUrl, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();

                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Accept", "application/json");

                yield return request.SendWebRequest();

                string responseText = request.downloadHandler != null
                    ? request.downloadHandler.text
                    : "";

                if (request.result != UnityWebRequest.Result.Success)
                {
                    lastServerError = request.error;

                    Debug.LogWarning("Backend request failed.");
                    Debug.LogWarning("HTTP code: " + request.responseCode);
                    Debug.LogWarning("Error: " + request.error);
                    Debug.LogWarning("Response: " + responseText);

                    isSending = false;
                    yield break;
                }

                if (logResponseJson)
                {
                    Debug.Log("Backend -> Unity JSON: " + responseText);
                }

                ParseAnalyzeResponse(responseText);

                lastSentAttention = attention;
                lastSentMeditation = meditation;
            }

            isSending = false;
        }

        private void ParseAnalyzeResponse(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                lastServerError = "Empty response from backend.";
                Debug.LogWarning(lastServerError);
                return;
            }

            try
            {
                AnalyzeResponse response = JsonUtility.FromJson<AnalyzeResponse>(json);

                if (response == null)
                {
                    lastServerError = "Cannot parse backend response.";
                    Debug.LogWarning(lastServerError);
                    return;
                }

                lastStatus = response.status;
                lastDetectedEmotion = response.detected_emotion;
                lastAiRecommendation = response.ai_recommendation;
                lastSessionToken = response.session_token;
                lastDetectionMethod = response.detection_method;
                lastRecommendationSource = response.recommendation_source;

                lastServerError = "";

                Debug.Log("Status: " + lastStatus);
                Debug.Log("Detected emotion: " + lastDetectedEmotion);
                Debug.Log("AI recommendation: " + lastAiRecommendation);
                Debug.Log("Session token: " + lastSessionToken);
                Debug.Log("Detection method: " + lastDetectionMethod);
                Debug.Log("Recommendation source: " + lastRecommendationSource);

                if (!string.IsNullOrEmpty(response.detail))
                {
                    Debug.LogWarning("Backend detail: " + response.detail);
                }

                if (!string.IsNullOrEmpty(response.error))
                {
                    Debug.LogWarning("Backend error: " + response.error);
                }

                if (!string.IsNullOrEmpty(response.message))
                {
                    Debug.LogWarning("Backend message: " + response.message);
                }
            }
            catch (Exception e)
            {
                lastServerError = e.Message;

                Debug.LogWarning("JSON response parse exception: " + e);
                Debug.LogWarning("Original response: " + json);
            }
        }

        private void OnGUI()
        {
            GUIStyle style = new GUIStyle(GUI.skin.label);
            style.fontSize = 20;
            style.normal.textColor = Color.white;
            style.wordWrap = true;

            GUILayout.BeginArea(new Rect(550, 20, 680, 650));

            GUILayout.Label("Backend response", style);
            GUILayout.Space(10);

            GUILayout.Label("Endpoint: " + endpointUrl, style);
            GUILayout.Label("Attention / Concentration: " + attention, style);
            GUILayout.Label("Meditation / Relaxation: " + meditation, style);
            GUILayout.Label("Poor Signal: " + poorSignal, style);

            GUILayout.Space(10);

            GUILayout.Label("Status: " + lastStatus, style);
            GUILayout.Label("Emotion: " + lastDetectedEmotion, style);
            GUILayout.Label("Recommendation: " + lastAiRecommendation, style);

            GUILayout.Space(10);

            GUILayout.Label("Session Token: " + lastSessionToken, style);
            GUILayout.Label("Detection Method: " + lastDetectionMethod, style);
            GUILayout.Label("Recommendation Source: " + lastRecommendationSource, style);

            if (!string.IsNullOrEmpty(lastServerError))
            {
                GUILayout.Space(10);
                GUILayout.Label("Error: " + lastServerError, style);
            }

            GUILayout.EndArea();
        }
    }
}