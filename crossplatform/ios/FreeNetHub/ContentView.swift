import SwiftUI
struct ContentView: View {
 var body: some View {
  VStack(spacing:16) {
   Text("FreeNet Hub 4.1.2").font(.largeTitle.bold())
   Text("NetworkExtension integration pack")
   Text("Provider core: NOT LINKED. The packet tunnel fails closed until a real forwarding core is integrated.").multilineTextAlignment(.center)
  }.padding()
 }
}
