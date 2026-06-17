using System;
using System.Threading;
using UnityEngine;
using System.Collections.Generic;
using MindWave.LitJson;
using System.Net.Sockets;
using System.Text;
using System.IO;

namespace MindWave
{
    public class TGCConnectionController : MonoBehaviour
    {
        private TcpClient client;
        private Stream stream;
        private byte[] buffer;

        private Thread connectionThread;
        private bool m_waitForExit = false;

        private string jsonBuffer = string.Empty;

        private readonly object threadLock = new object();
        private readonly object mainThreadActionsLock = new object();
        private readonly Queue<Action> mainThreadActions = new Queue<Action>();

        public delegate void UpdateIntValueDelegate(int value);
        public delegate void UpdateFloatValueDelegate(float value);

        public event UpdateIntValueDelegate UpdatePoorSignalEvent;
        public event UpdateIntValueDelegate UpdateAttentionEvent;
        public event UpdateIntValueDelegate UpdateMeditationEvent;
        public event UpdateIntValueDelegate UpdateRawdataEvent;
        public event UpdateIntValueDelegate UpdateBlinkEvent;

        public event UpdateFloatValueDelegate UpdateDeltaEvent;
        public event UpdateFloatValueDelegate UpdateThetaEvent;
        public event UpdateFloatValueDelegate UpdateLowAlphaEvent;
        public event UpdateFloatValueDelegate UpdateHighAlphaEvent;
        public event UpdateFloatValueDelegate UpdateLowBetaEvent;
        public event UpdateFloatValueDelegate UpdateHighBetaEvent;
        public event UpdateFloatValueDelegate UpdateLowGammaEvent;
        public event UpdateFloatValueDelegate UpdateHighGammaEvent;

        private void Start()
        {
            Connect();
        }

        private void Update()
        {
            while (true)
            {
                Action action = null;

                lock (mainThreadActionsLock)
                {
                    if (mainThreadActions.Count > 0)
                    {
                        action = mainThreadActions.Dequeue();
                    }
                }

                if (action == null)
                {
                    break;
                }

                action();
            }
        }

        public void Connect()
        {
            lock (threadLock)
            {
                if (connectionThread != null && connectionThread.IsAlive)
                {
                    Debug.Log("TGCConnectionController: already connected or connecting.");
                    return;
                }

                m_waitForExit = true;

                connectionThread = new Thread(ConnectionWorker);
                connectionThread.IsBackground = true;
                connectionThread.Start();
            }
        }

        public void Disconnect()
        {
            m_waitForExit = false;
            CloseConnection();
        }

        private void ConnectionWorker()
        {
            try
            {
                client = new TcpClient("127.0.0.1", 13854);
                stream = client.GetStream();
                buffer = new byte[4096];

                byte[] myWriteBuffer = Encoding.ASCII.GetBytes(@"{""enableRawOutput"": true, ""format"": ""Json""}");
                stream.Write(myWriteBuffer, 0, myWriteBuffer.Length);

                Debug.Log("TGCConnectionController: connected to ThinkGear Connector.");

                while (m_waitForExit)
                {
                    ParseData();
                }
            }
            catch (SocketException e)
            {
                Debug.Log("SocketException " + e);
            }
            catch (IOException e)
            {
                Debug.Log("IOException " + e);
            }
            catch (Exception e)
            {
                Debug.Log("Exception " + e);
            }
            finally
            {
                CloseConnection();
            }
        }

        private void CloseConnection()
        {
            try
            {
                if (stream != null)
                {
                    stream.Close();
                    stream = null;
                }
            }
            catch
            {
            }

            try
            {
                if (client != null)
                {
                    client.Close();
                    client = null;
                }
            }
            catch
            {
            }
        }

        public class PowerData
        {
            public float delta = 0;
            public float theta = 0;
            public float lowAlpha = 0;
            public float highAlpha = 0;
            public float lowBeta = 0;
            public float highBeta = 0;
            public float lowGamma = 0;
            public float highGamma = 0;

            public PowerData()
            {
            }
        }

        public class SenseData
        {
            public int attention = 0;
            public int meditation = 0;

            // Kept for compatibility, although in ThinkGear eegPower is usually NOT inside eSense.
            public PowerData eegPower = null;

            public SenseData()
            {
            }
        }

        public class PackatData
        {
            public string status = string.Empty;
            public int poorSignalLevel = 0;
            public int rawEeg = 0;
            public int blinkStrength = 0;

            public SenseData eSense = null;

            // In ThinkGear Connector, eegPower is usually here, at the top level of JSON.
            public PowerData eegPower = null;

            public PackatData()
            {
            }
        }

        private void ParseData()
        {
            if (stream == null || !stream.CanRead)
            {
                Thread.Sleep(10);
                return;
            }

            int bytesRead = stream.Read(buffer, 0, buffer.Length);

            if (bytesRead <= 0)
            {
                m_waitForExit = false;
                return;
            }

            string chunk = Encoding.ASCII.GetString(buffer, 0, bytesRead);

            if (string.IsNullOrEmpty(chunk))
            {
                return;
            }

            jsonBuffer += chunk;

            List<string> jsonObjects = ExtractCompleteJsonObjects();

            for (int i = 0; i < jsonObjects.Count; i++)
            {
                ParseJsonObject(jsonObjects[i]);
            }
        }

        private List<string> ExtractCompleteJsonObjects()
        {
            List<string> objects = new List<string>();

            int level = 0;
            int startIndex = -1;
            int lastCompleteEnd = 0;

            bool insideString = false;
            bool escaped = false;

            for (int i = 0; i < jsonBuffer.Length; i++)
            {
                char c = jsonBuffer[i];

                if (insideString)
                {
                    if (escaped)
                    {
                        escaped = false;
                    }
                    else if (c == '\\')
                    {
                        escaped = true;
                    }
                    else if (c == '"')
                    {
                        insideString = false;
                    }

                    continue;
                }

                if (c == '"')
                {
                    insideString = true;
                    continue;
                }

                if (c == '{')
                {
                    if (level == 0)
                    {
                        startIndex = i;
                    }

                    level++;
                }
                else if (c == '}')
                {
                    level--;

                    if (level == 0 && startIndex >= 0)
                    {
                        string jsonObject = jsonBuffer.Substring(startIndex, i - startIndex + 1);
                        objects.Add(jsonObject);

                        lastCompleteEnd = i + 1;
                        startIndex = -1;
                    }
                }
            }

            if (lastCompleteEnd > 0)
            {
                jsonBuffer = jsonBuffer.Substring(lastCompleteEnd);
            }

            // Protection against infinite buffer growth if garbage or corrupted JSON is received.
            if (jsonBuffer.Length > 20000)
            {
                jsonBuffer = string.Empty;
            }

            return objects;
        }

        private void ParseJsonObject(string json)
        {
            try
            {
                PackatData data = JsonMapper.ToObject<PackatData>(json);

                if (data == null)
                {
                    return;
                }

                ProcessPacket(data, json);
            }
            catch (Exception e)
            {
                Debug.Log("JSON parse exception: " + e);
                Debug.Log("Broken JSON: " + json);
            }
        }

        private bool JsonHasKey(string json, string key)
        {
            return json.IndexOf("\"" + key + "\"", StringComparison.Ordinal) >= 0;
        }

        private void ProcessPacket(PackatData data, string originalJson)
        {
            bool hasPoorSignal = JsonHasKey(originalJson, "poorSignalLevel");
            bool hasRawEeg = JsonHasKey(originalJson, "rawEeg");
            bool hasBlinkStrength = JsonHasKey(originalJson, "blinkStrength");

            if (hasPoorSignal)
            {
                int value = data.poorSignalLevel;

                EnqueueMainThreadAction(delegate
                {
                    if (UpdatePoorSignalEvent != null)
                    {
                        UpdatePoorSignalEvent(value);
                    }
                });
            }

            if (data.eSense != null)
            {
                int attention = data.eSense.attention;
                int meditation = data.eSense.meditation;

                EnqueueMainThreadAction(delegate
                {
                    if (UpdateAttentionEvent != null)
                    {
                        UpdateAttentionEvent(attention);
                    }

                    if (UpdateMeditationEvent != null)
                    {
                        UpdateMeditationEvent(meditation);
                    }
                });
            }

            PowerData power = data.eegPower;

            if (power == null && data.eSense != null)
            {
                power = data.eSense.eegPower;
            }

            if (power != null)
            {
                float delta = power.delta;
                float theta = power.theta;
                float lowAlpha = power.lowAlpha;
                float highAlpha = power.highAlpha;
                float lowBeta = power.lowBeta;
                float highBeta = power.highBeta;
                float lowGamma = power.lowGamma;
                float highGamma = power.highGamma;

                EnqueueMainThreadAction(delegate
                {
                    if (UpdateDeltaEvent != null)
                    {
                        UpdateDeltaEvent(delta);
                    }

                    if (UpdateThetaEvent != null)
                    {
                        UpdateThetaEvent(theta);
                    }

                    if (UpdateLowAlphaEvent != null)
                    {
                        UpdateLowAlphaEvent(lowAlpha);
                    }

                    if (UpdateHighAlphaEvent != null)
                    {
                        UpdateHighAlphaEvent(highAlpha);
                    }

                    if (UpdateLowBetaEvent != null)
                    {
                        UpdateLowBetaEvent(lowBeta);
                    }

                    if (UpdateHighBetaEvent != null)
                    {
                        UpdateHighBetaEvent(highBeta);
                    }

                    if (UpdateLowGammaEvent != null)
                    {
                        UpdateLowGammaEvent(lowGamma);
                    }

                    if (UpdateHighGammaEvent != null)
                    {
                        UpdateHighGammaEvent(highGamma);
                    }
                });
            }

            if (hasRawEeg)
            {
                int rawEeg = data.rawEeg;

                EnqueueMainThreadAction(delegate
                {
                    if (UpdateRawdataEvent != null)
                    {
                        UpdateRawdataEvent(rawEeg);
                    }
                });
            }

            if (hasBlinkStrength)
            {
                int blinkStrength = data.blinkStrength;

                EnqueueMainThreadAction(delegate
                {
                    if (UpdateBlinkEvent != null)
                    {
                        UpdateBlinkEvent(blinkStrength);
                    }
                });
            }
        }

        private void EnqueueMainThreadAction(Action action)
        {
            lock (mainThreadActionsLock)
            {
                mainThreadActions.Enqueue(action);
            }
        }

        private void OnDisable()
        {
            Disconnect();
        }

        private void OnApplicationQuit()
        {
            Disconnect();
        }
    }
}