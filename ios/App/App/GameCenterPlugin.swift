import UIKit
import Capacitor
import GameKit

// Game Center for the web game: sign-in, leaderboard scores, achievements and the dashboard.
// Registered in MainViewController; called from index.html as Capacitor.Plugins.GameCenter.
@objc(GameCenterPlugin)
public class GameCenterPlugin: CAPPlugin, CAPBridgedPlugin, GKGameCenterControllerDelegate {
    public let identifier = "GameCenterPlugin"
    public let jsName = "GameCenter"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "submitScore", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "reportAchievements", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "show", returnType: CAPPluginReturnPromise)
    ]
    private var waiting: [CAPPluginCall] = []
    private var asked = false

    @objc func signIn(_ call: CAPPluginCall) {
        let player = GKLocalPlayer.local
        if player.isAuthenticated { call.resolve(["signedIn": true]); return }
        waiting.append(call)
        if asked { return }
        asked = true
        // the handler can fire again later (e.g. after the settings app), so pending calls are answered each time
        player.authenticateHandler = { [weak self] vc, _ in
            guard let self = self else { return }
            if let vc = vc {
                DispatchQueue.main.async { self.bridge?.viewController?.present(vc, animated: true) }
                return
            }
            let ok = GKLocalPlayer.local.isAuthenticated
            let calls = self.waiting
            self.waiting = []
            for c in calls { c.resolve(["signedIn": ok]) }
        }
    }

    @objc func submitScore(_ call: CAPPluginCall) {
        guard GKLocalPlayer.local.isAuthenticated, let id = call.getString("leaderboard"), let score = call.getInt("score") else {
            call.resolve(["sent": false]); return
        }
        GKLeaderboard.submitScore(score, context: 0, player: GKLocalPlayer.local, leaderboardIDs: [id]) { error in
            call.resolve(["sent": error == nil])
        }
    }

    @objc func reportAchievements(_ call: CAPPluginCall) {
        guard GKLocalPlayer.local.isAuthenticated, let list = call.getArray("achievements", JSObject.self), !list.isEmpty else {
            call.resolve(["sent": false]); return
        }
        let items: [GKAchievement] = list.compactMap { item in
            guard let id = item["id"] as? String else { return nil }
            let a = GKAchievement(identifier: id)
            a.percentComplete = (item["percent"] as? Double) ?? 100
            a.showsCompletionBanner = true
            return a
        }
        GKAchievement.report(items) { error in call.resolve(["sent": error == nil]) }
    }

    @objc func show(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard GKLocalPlayer.local.isAuthenticated else { call.resolve(["shown": false]); return }
            let vc: GKGameCenterViewController
            if let id = call.getString("leaderboard") {
                vc = GKGameCenterViewController(leaderboardID: id, playerScope: .global, timeScope: .allTime)
            } else if call.getString("view") == "achievements" {
                vc = GKGameCenterViewController(state: .achievements)
            } else {
                vc = GKGameCenterViewController(state: .dashboard)
            }
            vc.gameCenterDelegate = self
            self.bridge?.viewController?.present(vc, animated: true)
            call.resolve(["shown": true])
        }
    }

    public func gameCenterViewControllerDidFinish(_ gameCenterViewController: GKGameCenterViewController) {
        gameCenterViewController.dismiss(animated: true)
    }
}

// The bridge with the app's own plugins (npm plugins register themselves).
class MainViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        bridge?.registerPluginInstance(GameCenterPlugin())
    }
}
