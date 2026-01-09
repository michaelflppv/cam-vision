import Flutter
import Foundation

final class PythonBridge: NSObject {
  static let shared = PythonBridge()

  private let runtime = PythonRuntime.shared
  private let frameHandler = PythonStreamHandler(methodName: "get_next_frame")
  private let eventHandler = PythonStreamHandler(methodName: "get_next_event")

  private override init() {}

  func register(with controller: FlutterViewController) {
    let methodChannel = FlutterMethodChannel(
      name: "securevision/python_bridge",
      binaryMessenger: controller.binaryMessenger
    )
    methodChannel.setMethodCallHandler(handleMethodCall)

    let frameChannel = FlutterEventChannel(
      name: "securevision/python_frames",
      binaryMessenger: controller.binaryMessenger
    )
    frameChannel.setStreamHandler(frameHandler)

    let eventChannel = FlutterEventChannel(
      name: "securevision/python_events",
      binaryMessenger: controller.binaryMessenger
    )
    eventChannel.setStreamHandler(eventHandler)
  }

  private func handleMethodCall(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    guard runtime.ensureInitialized() else {
      result(
        FlutterError(
          code: "python_unavailable",
          message: runtime.lastErrorMessage ?? "Python runtime unavailable.",
          details: ["method": call.method]
        )
      )
      return
    }

    switch call.method {
    case "initialize":
      let payload = jsonFromArgs(call.arguments)
      handlePythonResult(runtime.call(method: "initialize", args: [payload]), result: result)
    case "startCapture":
      let payload = jsonFromArgs(call.arguments)
      handlePythonResult(runtime.call(method: "start_capture", args: [payload]), result: result)
    case "stopCapture":
      handlePythonResult(runtime.call(method: "stop_capture", args: []), result: result)
    case "enrollFace":
      if let args = call.arguments as? [String: Any] {
        let personId = args["person_id"] as? String ?? ""
        let image = args["image_base64"] as? String ?? ""
        handlePythonResult(
          runtime.call(method: "enroll_face", args: [image, personId]),
          result: result
        )
      } else {
        result(
          FlutterError(
            code: "invalid_args",
            message: "Missing enrollment payload.",
            details: nil
          )
        )
      }
    case "updatePlateList":
      if let args = call.arguments as? [String: Any] {
        let listType = args["list_type"] as? String ?? ""
        let plates = args["plates"] as? [String] ?? []
        let payload = jsonString(from: plates) ?? "[]"
        handlePythonResult(
          runtime.call(method: "update_plate_list", args: [listType, payload]),
          result: result
        )
      } else {
        result(
          FlutterError(
            code: "invalid_args",
            message: "Missing plate list payload.",
            details: nil
          )
        )
      }
    default:
      result(FlutterMethodNotImplemented)
    }
  }

  private func jsonFromArgs(_ args: Any?) -> String {
    guard let map = args as? [String: Any] else {
      return "{}"
    }
    return jsonString(from: map) ?? "{}"
  }

  private func handlePythonResult(_ payload: String?, result: @escaping FlutterResult) {
    guard let payload = payload else {
      result(
        FlutterError(
          code: "python_error",
          message: runtime.lastErrorMessage ?? "Python returned empty response.",
          details: nil
        )
      )
      return
    }
    if let json = parseJson(payload),
       let status = json["status"] as? String,
       status == "error" {
      result(
        FlutterError(
          code: "python_error",
          message: json["message"] as? String ?? "Python error",
          details: json
        )
      )
      return
    }
    result(nil)
  }
}

final class PythonStreamHandler: NSObject, FlutterStreamHandler {
  private let methodName: String
  private var timer: Timer?
  private var eventSink: FlutterEventSink?
  private let runtime = PythonRuntime.shared

  init(methodName: String) {
    self.methodName = methodName
  }

  func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink)
    -> FlutterError? {
    eventSink = events
    startPolling()
    return nil
  }

  func onCancel(withArguments arguments: Any?) -> FlutterError? {
    stopPolling()
    eventSink = nil
    return nil
  }

  private func startPolling() {
    guard timer == nil else {
      return
    }
    timer = Timer.scheduledTimer(withTimeInterval: 0.033, repeats: true) { [weak self] _ in
      self?.pollOnce()
    }
  }

  private func stopPolling() {
    timer?.invalidate()
    timer = nil
  }

  private func pollOnce() {
    guard runtime.ensureInitialized() else {
      return
    }
    guard let payload = runtime.call(method: methodName, args: []) else {
      return
    }
    guard let json = parseJson(payload) else {
      return
    }
    if let status = json["status"] as? String, status == "empty" {
      return
    }
    if let messageType = json["type"] as? String, messageType == "frame" || messageType == "event"
    {
      DispatchQueue.main.async { [weak self] in
        self?.eventSink?(payload)
      }
    }
  }
}

#if canImport(Python)
import Python

final class PythonRuntime {
  static let shared = PythonRuntime()

  private var initialized = false
  private var module: UnsafeMutablePointer<PyObject>?
  private(set) var lastErrorMessage: String?

  private init() {}

  func ensureInitialized() -> Bool {
    if initialized {
      return module != nil
    }
    configureEnvironment()
    Py_Initialize()
    let moduleName = "cv_bridge"
    moduleName.withCString { cString in
      module = PyImport_ImportModule(cString)
    }
    if module == nil {
      PyErr_Print()
      lastErrorMessage = "Unable to import cv_bridge. Ensure Python runtime is bundled."
    }
    initialized = true
    return module != nil
  }

  func call(method: String, args: [String]) -> String? {
    guard let module = module else {
      lastErrorMessage = "Python module not loaded."
      return nil
    }
    guard let function = method.withCString({ PyObject_GetAttrString(module, $0) }) else {
      lastErrorMessage = "Python function not found: \(method)"
      return nil
    }
    let tuple = PyTuple_New(args.count)
    for (index, value) in args.enumerated() {
      let pyString = value.withCString { PyUnicode_FromString($0) }
      PyTuple_SetItem(tuple, index, pyString)
    }
    guard let result = PyObject_CallObject(function, tuple) else {
      PyErr_Print()
      lastErrorMessage = "Python call failed: \(method)"
      Py_DecRef(function)
      Py_DecRef(tuple)
      return nil
    }
    Py_DecRef(function)
    Py_DecRef(tuple)
    defer { Py_DecRef(result) }
    guard let resultStr = PyObject_Str(result) else {
      lastErrorMessage = "Python returned non-string response."
      return nil
    }
    defer { Py_DecRef(resultStr) }
    guard let cString = PyUnicode_AsUTF8(resultStr) else {
      lastErrorMessage = "Failed to decode Python response."
      return nil
    }
    return String(cString: cString)
  }

  private func configureEnvironment() {
    let resourcePath = Bundle.main.resourcePath ?? ""
    let stdlibPath = "\(resourcePath)/python-stdlib"
    let sitePackages = "\(resourcePath)/python-stdlib/site-packages"
    let bundledPath = "\(resourcePath)/python"
    let pythonPath = [stdlibPath, sitePackages, bundledPath].joined(separator: ":")

    setenv("PYTHONHOME", resourcePath, 1)
    setenv("PYTHONPATH", pythonPath, 1)
  }
}
#else
final class PythonRuntime {
  static let shared = PythonRuntime()

  private(set) var lastErrorMessage: String? =
    "Python runtime not linked. Add Python.xcframework (Python-Apple-Support)."

  private init() {}

  func ensureInitialized() -> Bool {
    return false
  }

  func call(method: String, args: [String]) -> String? {
    return nil
  }
}
#endif

private func parseJson(_ payload: String) -> [String: Any]? {
  guard let data = payload.data(using: .utf8) else {
    return nil
  }
  return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
}

private func jsonString(from value: Any) -> String? {
  guard JSONSerialization.isValidJSONObject(value) else {
    return nil
  }
  guard let data = try? JSONSerialization.data(withJSONObject: value) else {
    return nil
  }
  return String(data: data, encoding: .utf8)
}
