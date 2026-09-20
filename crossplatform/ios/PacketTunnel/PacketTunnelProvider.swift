import NetworkExtension
final class PacketTunnelProvider: NEPacketTunnelProvider {
 enum ProviderError: Error { case coreNotLinked }
 override func startTunnel(options: [String:NSObject]?, completionHandler: @escaping (Error?)->Void) { completionHandler(ProviderError.coreNotLinked) }
 override func stopTunnel(with reason: NEProviderStopReason, completionHandler: @escaping ()->Void) { completionHandler() }
}
