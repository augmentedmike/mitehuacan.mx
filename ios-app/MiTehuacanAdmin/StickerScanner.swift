import SwiftUI
import AVFoundation
import UIKit

/// A live camera QR scanner. Wraps an AVCaptureSession that watches for `.qr`
/// metadata and calls `onCode` with the first payload it reads. SwiftUI-friendly:
/// drop `QRScannerView { code in … }` into a sheet. Handles the permission prompt
/// and reports the not-authorized case so the caller can offer manual entry.
struct QRScannerView: UIViewControllerRepresentable {
    var onCode: (String) -> Void
    var onDenied: () -> Void = {}

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> ScannerVC {
        let vc = ScannerVC()
        vc.onCode = { code in onCode(code) }
        vc.onDenied = onDenied
        return vc
    }
    func updateUIViewController(_ vc: ScannerVC, context: Context) {}

    final class Coordinator: NSObject { init(_ parent: QRScannerView) {} }

    final class ScannerVC: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
        var onCode: ((String) -> Void)?
        var onDenied: (() -> Void)?
        private let session = AVCaptureSession()
        private var preview: AVCaptureVideoPreviewLayer?
        private var delivered = false          // fire once; the sheet dismisses after

        override func viewDidLoad() {
            super.viewDidLoad()
            view.backgroundColor = .black
            switch AVCaptureDevice.authorizationStatus(for: .video) {
            case .authorized: configure()
            case .notDetermined:
                AVCaptureDevice.requestAccess(for: .video) { [weak self] ok in
                    DispatchQueue.main.async { ok ? self?.configure() : self?.onDenied?() }
                }
            default: onDenied?()
            }
        }

        private func configure() {
            guard let device = AVCaptureDevice.default(for: .video),
                  let input = try? AVCaptureDeviceInput(device: device),
                  session.canAddInput(input) else { onDenied?(); return }
            session.addInput(input)
            let output = AVCaptureMetadataOutput()
            guard session.canAddOutput(output) else { onDenied?(); return }
            session.addOutput(output)
            output.setMetadataObjectsDelegate(self, queue: .main)
            output.metadataObjectTypes = [.qr]

            let layer = AVCaptureVideoPreviewLayer(session: session)
            layer.videoGravity = .resizeAspectFill
            layer.frame = view.layer.bounds
            view.layer.addSublayer(layer)
            preview = layer

            DispatchQueue.global(qos: .userInitiated).async { [weak self] in self?.session.startRunning() }
        }

        override func viewDidLayoutSubviews() {
            super.viewDidLayoutSubviews()
            preview?.frame = view.layer.bounds
        }

        override func viewWillDisappear(_ animated: Bool) {
            super.viewWillDisappear(animated)
            if session.isRunning { session.stopRunning() }
        }

        func metadataOutput(_ output: AVCaptureMetadataOutput,
                            didOutput objects: [AVMetadataObject],
                            from connection: AVCaptureConnection) {
            guard !delivered,
                  let obj = objects.first as? AVMetadataMachineReadableCodeObject,
                  let value = obj.stringValue else { return }
            delivered = true
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            onCode?(value)
        }
    }
}
