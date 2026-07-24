import Foundation
import Security
import Combine

/// The admin identity for the app: user "michael" + a PIN (the account password).
/// The PIN is entered at runtime and kept in the iOS Keychain — never in source.
/// Unlock validates against /api/admin/login; once unlocked, the stored token is
/// sent as `Authorization: Bearer` on every write. Recording/viewing don't need it;
/// only reconcile (pushing to production) does.
@MainActor
final class AdminAuth: ObservableObject {
    static let user = "michael"
    static let base = "https://mitehuacan.mx"

    @Published var unlocked = false
    @Published var error = ""
    @Published var busy = false

    private let kcKey = "mx.mitehuacan.admin.token"

    init() { unlocked = (token != nil) }

    /// The bearer token (= the admin password), stored only in the Keychain.
    var token: String? {
        get { Keychain.read(kcKey) }
        set { newValue == nil ? Keychain.delete(kcKey) : Keychain.write(kcKey, newValue!) }
    }

    /// Validate the PIN with the server; on success store it and unlock. If offline
    /// but a token is already stored (validated before), unlock locally so recording
    /// keeps working — the push will authenticate when back online.
    func unlock(pin: String) async -> Bool {
        error = ""; busy = true; defer { busy = false }
        guard var req = try? loginRequest(pin) else { error = "Error interno"; return false }
        req.timeoutInterval = 12
        do {
            let (_, resp) = try await URLSession.shared.data(for: req)
            if (resp as? HTTPURLResponse)?.statusCode == 200 {
                token = pin; unlocked = true; return true
            }
            error = "PIN incorrecto"
            return false
        } catch {
            if token != nil { unlocked = true; return true }   // offline, prior session
            self.error = "Sin conexión y sin sesión guardada — conéctate una vez para iniciar."
            return false
        }
    }

    func lock() { unlocked = false }          // keep the token; just re-prompt
    func signOut() { token = nil; unlocked = false }

    private func loginRequest(_ pin: String) throws -> URLRequest {
        var req = URLRequest(url: URL(string: "\(Self.base)/api/admin/login")!)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: ["user": Self.user, "pass": pin])
        return req
    }
}

/// Minimal Keychain wrapper (generic password items).
enum Keychain {
    static func write(_ key: String, _ value: String) {
        let base: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrAccount as String: key]
        SecItemDelete(base as CFDictionary)
        var add = base
        add[kSecValueData as String] = Data(value.utf8)
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        SecItemAdd(add as CFDictionary, nil)
    }
    static func read(_ key: String) -> String? {
        let q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrAccount as String: key,
                                kSecReturnData as String: true,
                                kSecMatchLimit as String: kSecMatchLimitOne]
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess,
              let d = out as? Data else { return nil }
        return String(data: d, encoding: .utf8)
    }
    static func delete(_ key: String) {
        SecItemDelete([kSecClass as String: kSecClassGenericPassword,
                       kSecAttrAccount as String: key] as CFDictionary)
    }
}
