using UnityEngine;

namespace MindWave
{
    public class DisplayData : MonoBehaviour
    {
        public Texture2D[] signalIcons;

        private int indexSignalIcons = 1;

        private TGCConnectionController controller;

        private int poorSignal1;
        private int attention1;
        private int meditation1;
        private int rawEeg1;
        private int blinkStrength1;

        private float delta;
        private float theta;
        private float lowAlpha;
        private float highAlpha;
        private float lowBeta;
        private float highBeta;
        private float lowGamma;
        private float highGamma;

        private string connectionStatus = "Controller not found";

        private void Start()
        {
            controller = FindObjectOfType<TGCConnectionController>();

            if (controller == null)
            {
                Debug.LogError("DisplayData: TGCConnectionController not found in scene.");
                connectionStatus = "TGCConnectionController not found";
                return;
            }

            connectionStatus = "Controller found";

            controller.UpdatePoorSignalEvent += OnUpdatePoorSignal;
            controller.UpdateAttentionEvent += OnUpdateAttention;
            controller.UpdateMeditationEvent += OnUpdateMeditation;
            controller.UpdateRawdataEvent += OnUpdateRawEeg;
            controller.UpdateBlinkEvent += OnUpdateBlink;

            controller.UpdateDeltaEvent += OnUpdateDelta;
            controller.UpdateThetaEvent += OnUpdateTheta;
            controller.UpdateLowAlphaEvent += OnUpdateLowAlpha;
            controller.UpdateHighAlphaEvent += OnUpdateHighAlpha;
            controller.UpdateLowBetaEvent += OnUpdateLowBeta;
            controller.UpdateHighBetaEvent += OnUpdateHighBeta;
            controller.UpdateLowGammaEvent += OnUpdateLowGamma;
            controller.UpdateHighGammaEvent += OnUpdateHighGamma;
        }

        private void OnDestroy()
        {
            if (controller == null)
            {
                return;
            }

            controller.UpdatePoorSignalEvent -= OnUpdatePoorSignal;
            controller.UpdateAttentionEvent -= OnUpdateAttention;
            controller.UpdateMeditationEvent -= OnUpdateMeditation;
            controller.UpdateRawdataEvent -= OnUpdateRawEeg;
            controller.UpdateBlinkEvent -= OnUpdateBlink;

            controller.UpdateDeltaEvent -= OnUpdateDelta;
            controller.UpdateThetaEvent -= OnUpdateTheta;
            controller.UpdateLowAlphaEvent -= OnUpdateLowAlpha;
            controller.UpdateHighAlphaEvent -= OnUpdateHighAlpha;
            controller.UpdateLowBetaEvent -= OnUpdateLowBeta;
            controller.UpdateHighBetaEvent -= OnUpdateHighBeta;
            controller.UpdateLowGammaEvent -= OnUpdateLowGamma;
            controller.UpdateHighGammaEvent -= OnUpdateHighGamma;
        }

        private void OnUpdatePoorSignal(int value)
        {
            poorSignal1 = value;

            if (value < 25)
            {
                indexSignalIcons = 0;
            }
            else if (value >= 25 && value < 51)
            {
                indexSignalIcons = 4;
            }
            else if (value >= 51 && value < 78)
            {
                indexSignalIcons = 3;
            }
            else if (value >= 78 && value < 107)
            {
                indexSignalIcons = 2;
            }
            else
            {
                indexSignalIcons = 1;
            }
        }

        private void OnUpdateAttention(int value)
        {
            attention1 = value;
        }

        private void OnUpdateMeditation(int value)
        {
            meditation1 = value;
        }

        private void OnUpdateRawEeg(int value)
        {
            rawEeg1 = value;
        }

        private void OnUpdateBlink(int value)
        {
            blinkStrength1 = value;
        }

        private void OnUpdateDelta(float value)
        {
            delta = value;
        }

        private void OnUpdateTheta(float value)
        {
            theta = value;
        }

        private void OnUpdateLowAlpha(float value)
        {
            lowAlpha = value;
        }

        private void OnUpdateHighAlpha(float value)
        {
            highAlpha = value;
        }

        private void OnUpdateLowBeta(float value)
        {
            lowBeta = value;
        }

        private void OnUpdateHighBeta(float value)
        {
            highBeta = value;
        }

        private void OnUpdateLowGamma(float value)
        {
            lowGamma = value;
        }

        private void OnUpdateHighGamma(float value)
        {
            highGamma = value;
        }

        private void OnGUI()
        {
            GUIStyle style = new GUIStyle(GUI.skin.label);
            style.fontSize = 22;
            style.normal.textColor = Color.white;

            GUILayout.BeginArea(new Rect(20, 20, 500, 650));

            GUILayout.Label("MindWave data", style);
            GUILayout.Space(10);

            if (controller == null)
            {
                GUILayout.Label("Status: " + connectionStatus, style);
                GUILayout.EndArea();
                return;
            }

            GUILayout.BeginHorizontal();

            if (GUILayout.Button("Connect", GUILayout.Width(120), GUILayout.Height(40)))
            {
                controller.Connect();
                connectionStatus = "Connect pressed";
            }

            if (GUILayout.Button("Disconnect", GUILayout.Width(120), GUILayout.Height(40)))
            {
                controller.Disconnect();
                indexSignalIcons = 1;
                connectionStatus = "Disconnected";
            }

            GUILayout.EndHorizontal();

            GUILayout.Space(15);

            GUILayout.Label("Status: " + connectionStatus, style);
            GUILayout.Label("Poor Signal: " + poorSignal1, style);
            GUILayout.Label("Attention: " + attention1, style);
            GUILayout.Label("Meditation: " + meditation1, style);
            GUILayout.Label("Raw EEG: " + rawEeg1, style);
            GUILayout.Label("Blink: " + blinkStrength1, style);

            GUILayout.Space(15);

            GUILayout.Label("Delta: " + delta, style);
            GUILayout.Label("Theta: " + theta, style);
            GUILayout.Label("Low Alpha: " + lowAlpha, style);
            GUILayout.Label("High Alpha: " + highAlpha, style);
            GUILayout.Label("Low Beta: " + lowBeta, style);
            GUILayout.Label("High Beta: " + highBeta, style);
            GUILayout.Label("Low Gamma: " + lowGamma, style);
            GUILayout.Label("High Gamma: " + highGamma, style);

            GUILayout.Space(15);

            if (signalIcons != null &&
                signalIcons.Length > indexSignalIcons &&
                signalIcons[indexSignalIcons] != null)
            {
                GUILayout.Label(signalIcons[indexSignalIcons], GUILayout.Width(64), GUILayout.Height(64));
            }
            else
            {
                GUILayout.Label("Signal icon index: " + indexSignalIcons, style);
                GUILayout.Label("Icons are not assigned", style);
            }

            GUILayout.EndArea();
        }
    }
}