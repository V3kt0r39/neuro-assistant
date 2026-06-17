# YUI NeuroSky Unity Client

Unity client for the **YUI** project. The project connects Unity to the NeuroSky MindWave / ThinkGear data stream, displays EEG-related values in a Unity scene, and can optionally forward selected values to a backend API for emotion detection, recommendations, or session processing.

## Overview

This project provides the client-side neurointerface layer for YUI.

It includes:

- TCP connection to ThinkGear Connector.
- Real-time parsing of NeuroSky MindWave JSON packets.
- Display of attention, meditation, raw EEG, blink strength, poor signal level, and EEG power bands.
- Signal status icons for visual feedback.
- Optional HTTP POST integration with a backend service.
- A Unity scene and prefab setup for quick testing.

## Correct Unity Project Structure

The Unity project should be opened from the root folder:

```text
YUI/
```

The expected structure is:

```text
YUI/
  Assets/
    NeuroSkyAssets/
      NeuroSkyScripts/
        Author.cs
        DisplayData.cs
        MindWaveHttpSender.cs
        PreserveGameObject.cs
        TGCConnectionController.cs
        LitJson/
      NeuroSkySignalIcons/
        signal_connected.png
        signal_disconnected.png
        signal_fitting1.png
        signal_fitting2.png
        signal_fitting3.png
      NeuroSkyTGCCController/
        NeuroSkyTGCCController.prefab
      Scenes/
        TheScene.unity
    Scenes/
      SampleScene.unity
  Packages/
  ProjectSettings/
  README.md
```

The `NeuroSkyAssets` folder must be located directly inside the main Unity `Assets` folder:

```text
YUI/Assets/NeuroSkyAssets/
```

This structure is incorrect and should be avoided:

```text
YUI/Assets/Assets/NeuroSkyAssets/
```

Do not open `YUI/Assets/` as a Unity project. Always open the root folder `YUI/`.

## Main Components

### TGCConnectionController

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/TGCConnectionController.cs
```

`TGCConnectionController` is the main MindWave connection controller.

It performs the following tasks:

- Connects to ThinkGear Connector at `127.0.0.1:13854`.
- Enables raw JSON output.
- Reads the incoming TCP data stream.
- Extracts complete JSON objects from the stream.
- Parses NeuroSky data packets.
- Publishes parsed values through Unity events.
- Uses a background thread for socket communication.
- Queues parsed updates back onto Unity's main thread.

The controller exposes events for:

```text
UpdatePoorSignalEvent
UpdateAttentionEvent
UpdateMeditationEvent
UpdateRawdataEvent
UpdateBlinkEvent
UpdateDeltaEvent
UpdateThetaEvent
UpdateLowAlphaEvent
UpdateHighAlphaEvent
UpdateLowBetaEvent
UpdateHighBetaEvent
UpdateLowGammaEvent
UpdateHighGammaEvent
```

This component should be present in the active scene.

### DisplayData

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/DisplayData.cs
```

`DisplayData` is a simple debug UI component for displaying MindWave data inside Unity.

It:

- Finds `TGCConnectionController` in the scene.
- Subscribes to the controller's update events.
- Displays current MindWave values using Unity `OnGUI`.
- Provides `Connect` and `Disconnect` buttons.
- Shows the current signal icon based on poor signal level.

The component displays:

- Poor Signal
- Attention
- Meditation
- Raw EEG
- Blink Strength
- Delta
- Theta
- Low Alpha
- High Alpha
- Low Beta
- High Beta
- Low Gamma
- High Gamma

The `signalIcons` array should be assigned in the Unity Inspector.

Recommended icon order:

```text
0 - signal_connected.png
1 - signal_disconnected.png
2 - signal_fitting1.png
3 - signal_fitting2.png
4 - signal_fitting3.png
```

### MindWaveHttpSender

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/MindWaveHttpSender.cs
```

`MindWaveHttpSender` sends selected MindWave values to a backend API.

It listens to:

- Attention
- Meditation
- Poor Signal

Then it sends them as JSON using HTTP POST.

Unity values are mapped to backend fields as follows:

```text
attention  -> concentration
meditation -> relaxation
poorSignal -> poor_signal
```

Example request:

```json
{
  "concentration": 65,
  "relaxation": 42,
  "poor_signal": 0
}
```

Before using this component, replace the default endpoint value:

```csharp
public string endpointUrl = "Your-admin-or-ip-addres";
```

with the real backend endpoint, for example:

```csharp
public string endpointUrl = "http://127.0.0.1:8000/analyze";
```

The correct endpoint depends on the backend part of the YUI system.

The component can also display backend response fields, including:

- Status
- Detected emotion
- AI recommendation
- Session token
- Detection method
- Recommendation source
- Server error text

### PreserveGameObject

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/PreserveGameObject.cs
```

`PreserveGameObject` keeps a GameObject alive when Unity loads another scene.

It calls:

```csharp
DontDestroyOnLoad(gameObject);
```

Use this component if the MindWave controller object must persist across scenes.

### Author

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/Author.cs
```

This script contains author-related project information. It does not affect runtime behavior.

### LitJson

Location:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/LitJson/
```

The `LitJson` folder is required by `TGCConnectionController`.

The controller uses:

```csharp
using MindWave.LitJson;
```

If this folder is missing or incorrectly placed, Unity may show compile errors related to `JsonMapper` or the `MindWave.LitJson` namespace.

## Scene Setup

Open the main NeuroSky scene:

```text
Assets/NeuroSkyAssets/Scenes/TheScene.unity
```

The scene should contain an object with:

```text
TGCConnectionController
```

The scene should also contain an object with:

```text
DisplayData
```

Optionally, add an object with:

```text
MindWaveHttpSender
```

if backend communication is required.

## Quick Start

1. Open Unity Hub.
2. Add the project using the root folder:

   ```text
   YUI/
   ```

3. Make sure `NeuroSkyAssets` is located here:

   ```text
   YUI/Assets/NeuroSkyAssets/
   ```

4. Open the scene:

   ```text
   Assets/NeuroSkyAssets/Scenes/TheScene.unity
   ```

5. Start ThinkGear Connector.
6. Connect the NeuroSky MindWave headset.
7. Start Play Mode in Unity.
8. If the connection does not start automatically, press `Connect`.
9. Check the displayed data in the Unity Game view and Unity Console.

## Backend Integration

The backend integration is optional.

When `MindWaveHttpSender` is enabled, Unity sends requests to the configured `endpointUrl`.

Request payload:

```json
{
  "concentration": 65,
  "relaxation": 42,
  "poor_signal": 0
}
```

Expected successful response example:

```json
{
  "status": "ok",
  "detected_emotion": "focused",
  "ai_recommendation": "Continue current activity",
  "session_token": "example-token",
  "detection_method": "example-method",
  "recommendation_source": "example-source"
}
```

Supported error fields:

```json
{
  "detail": "error details",
  "error": "error text",
  "message": "message text"
}
```

## MindWaveHttpSender Settings

The following fields are configurable in the Unity Inspector:

```text
Endpoint Url
Send Interval
Send Only When Values Changed
Log Request Json
Log Response Json
```

### Endpoint Url

Backend API endpoint used for POST requests.

### Send Interval

Controls how often Unity sends data to the backend.

Example:

```text
1.0 = once per second
0.5 = twice per second
```

### Send Only When Values Changed

If enabled, Unity sends a request only when attention or meditation values change.

### Log Request Json

If enabled, Unity logs outgoing request JSON to the Console.

### Log Response Json

If enabled, Unity logs backend response JSON to the Console.

## Signal Quality Handling

The project uses `poorSignalLevel` to determine connection quality.

In `MindWaveHttpSender`, requests are skipped when:

```text
poorSignal >= 200
```

This prevents sending unreliable or garbage values to the backend.

In `DisplayData`, signal icons are selected according to the current poor signal value.

## Requirements

- Unity project with `Assets`, `Packages`, and `ProjectSettings`.
- NeuroSky MindWave or compatible headset.
- ThinkGear Connector.
- Local TCP access to:

  ```text
  127.0.0.1:13854
  ```

- Backend API, if `MindWaveHttpSender` is used.

The exact Unity version is not specified in the provided files. It is recommended to open the project with the Unity version originally used for development or with a compatible version.

## Troubleshooting

### Unity does not see NeuroSkyAssets

Check the folder path.

Incorrect:

```text
YUI/Assets/Assets/NeuroSkyAssets/
```

Correct:

```text
YUI/Assets/NeuroSkyAssets/
```

Move the full `NeuroSkyAssets` folder together with its `.meta` file.

### DisplayData shows "TGCConnectionController not found"

The active scene does not contain a GameObject with the `TGCConnectionController` component.

Add the prefab or create a new GameObject and attach `TGCConnectionController`.

### Connection to 127.0.0.1:13854 fails

Check the following:

- ThinkGear Connector is running.
- The MindWave headset is connected.
- Port `13854` is not blocked.
- Firewall is not blocking local TCP connections.
- The headset is visible inside ThinkGear Connector.

### JsonMapper or MindWave.LitJson compile errors

Check that this folder exists:

```text
Assets/NeuroSkyAssets/NeuroSkyScripts/LitJson/
```

Do not remove or rename the `LitJson` folder unless the code is updated accordingly.

### Signal icons are not displayed

Check the `signalIcons` array in the `DisplayData` component.

Recommended order:

```text
0 - signal_connected.png
1 - signal_disconnected.png
2 - signal_fitting1.png
3 - signal_fitting2.png
4 - signal_fitting3.png
```

### Backend request failed

Check the following:

- `endpointUrl` is set to a real backend URL.
- Backend server is running.
- The endpoint accepts POST requests.
- The backend accepts JSON with `concentration`, `relaxation`, and `poor_signal`.
- Unity can access the backend URL.
- Firewall or network settings are not blocking the request.

## Development Notes

- Keep Unity `.meta` files when moving assets.
- Do not move scripts without their corresponding `.meta` files.
- Avoid nested `Assets/Assets` project structures.
- Check Unity Console after every import or folder move.
- The current debug UI uses `OnGUI`; for production UI, consider replacing it with Unity Canvas or UI Toolkit.
- Backend configuration should eventually be moved to a safer configuration layer such as a ScriptableObject, environment-specific config, or external settings file.

## Author

The project files identify the author as:

```text
Kosyagami (King_Hold)
```

## License

No license file was provided with the uploaded project files.

Before publishing or distributing the project, add a `LICENSE` file or clearly specify usage terms in this README.
