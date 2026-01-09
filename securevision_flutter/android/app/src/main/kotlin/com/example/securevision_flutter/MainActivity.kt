package com.example.securevision_flutter

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import org.json.JSONObject

class MainActivity : FlutterActivity() {
    private lateinit var pythonBridge: PythonBridge

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        pythonBridge = PythonBridge(applicationContext)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, BRIDGE_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "initialize" -> {
                        val configJson = jsonFromArgs(call)
                        val response = pythonBridge.initialize(configJson)
                        handleControlResponse(result, response)
                    }
                    "startCapture" -> {
                        val sourceJson = jsonFromArgs(call)
                        val response = pythonBridge.startCapture(sourceJson)
                        handleControlResponse(result, response)
                    }
                    "stopCapture" -> {
                        val response = pythonBridge.stopCapture()
                        handleControlResponse(result, response)
                    }
                    "enrollFace" -> {
                        val args = call.arguments as? Map<*, *> ?: emptyMap<String, Any>()
                        val personId = args["person_id"]?.toString().orEmpty()
                        val imageBase64 = args["image_base64"]?.toString().orEmpty()
                        val response = pythonBridge.enrollFace(imageBase64, personId)
                        handleControlResponse(result, response)
                    }
                    "updatePlateList" -> {
                        val args = call.arguments as? Map<*, *> ?: emptyMap<String, Any>()
                        val listType = args["list_type"]?.toString().orEmpty()
                        val rawPlates = args["plates"] as? List<*> ?: emptyList<Any>()
                        val plates = rawPlates.map { it.toString() }
                        val response = pythonBridge.updatePlateList(listType, plates)
                        handleControlResponse(result, response)
                    }
                    else -> result.notImplemented()
                }
            }

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, FRAME_CHANNEL)
            .setStreamHandler(PythonStreamHandler(pythonBridge::getNextFrame))

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, EVENT_CHANNEL)
            .setStreamHandler(PythonStreamHandler(pythonBridge::getNextEvent))
    }

    private fun jsonFromArgs(call: MethodCall): String {
        val args = call.arguments
        if (args is Map<*, *>) {
            return JSONObject(args).toString()
        }
        return "{}"
    }

    private fun handleControlResponse(
        result: MethodChannel.Result,
        response: PythonResponse
    ) {
        if (response.status == "error") {
            result.error("python_error", response.message ?: "error", null)
        } else {
            result.success(null)
        }
    }

    private class PythonBridge(private val context: Context) {
        private val python: Python by lazy {
            if (!Python.isStarted()) {
                Python.start(AndroidPlatform(context))
            }
            Python.getInstance()
        }
        private val module: PyObject by lazy { python.getModule("cv_bridge") }

        fun initialize(configJson: String): PythonResponse {
            return parseResponse(call("initialize", configJson))
        }

        fun startCapture(sourceJson: String): PythonResponse {
            return parseResponse(call("start_capture", sourceJson))
        }

        fun stopCapture(): PythonResponse {
            return parseResponse(call("stop_capture"))
        }

        fun enrollFace(imageBase64: String, personId: String): PythonResponse {
            return parseResponse(call("enroll_face", imageBase64, personId))
        }

        fun updatePlateList(listType: String, plates: List<String>): PythonResponse {
            return parseResponse(call("update_plate_list", listType, plates))
        }

        fun getNextFrame(): String = call("get_next_frame")

        fun getNextEvent(): String = call("get_next_event")

        private fun call(method: String, vararg args: Any): String {
            return module.callAttr(method, *args).toString()
        }

        private fun parseResponse(payload: String): PythonResponse {
            return try {
                val json = JSONObject(payload)
                PythonResponse(json.optString("status"), json.optString("message"))
            } catch (_: Exception) {
                PythonResponse("error", "invalid_python_response")
            }
        }
    }

    private data class PythonResponse(val status: String, val message: String? = null)

    private class PythonStreamHandler(
        private val poller: () -> String
    ) : EventChannel.StreamHandler {
        private val executor = Executors.newSingleThreadScheduledExecutor()
        private val handler = Handler(Looper.getMainLooper())
        private var future: ScheduledFuture<*>? = null
        private var sink: EventChannel.EventSink? = null

        override fun onListen(arguments: Any?, events: EventChannel.EventSink) {
            sink = events
            startPolling()
        }

        override fun onCancel(arguments: Any?) {
            stopPolling()
            sink = null
        }

        private fun startPolling() {
            if (future != null) {
                return
            }
            future = executor.scheduleAtFixedRate(
                { pollOnce() },
                0,
                33,
                TimeUnit.MILLISECONDS
            )
        }

        private fun stopPolling() {
            future?.cancel(true)
            future = null
        }

        private fun pollOnce() {
            val payload = poller()
            try {
                val json = JSONObject(payload)
                val status = json.optString("status")
                if (status == "empty") {
                    return
                }
                val messageType = json.optString("type")
                if (messageType == "frame" || messageType == "event") {
                    handler.post { sink?.success(payload) }
                } else if (status == "error") {
                    Log.w(TAG, "Python error: ${json.optString("message")}")
                }
            } catch (exc: Exception) {
                Log.w(TAG, "Invalid Python payload: $payload", exc)
            }
        }
    }

    companion object {
        private const val TAG = "SecureVisionBridge"
        private const val BRIDGE_CHANNEL = "securevision/python_bridge"
        private const val FRAME_CHANNEL = "securevision/python_frames"
        private const val EVENT_CHANNEL = "securevision/python_events"
    }
}
