import Foundation

guard let resourcesURL = Bundle.main.resourceURL else {
    fputs("Could not locate application resources.\n", stderr)
    exit(1)
}

let commandURL = resourcesURL.appendingPathComponent("launch.command")
let process = Process()
process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
process.arguments = ["-a", "Terminal", commandURL.path]

do {
    try process.run()
    process.waitUntilExit()
    exit(process.terminationStatus)
} catch {
    fputs("Could not open Terminal: \(error)\n", stderr)
    exit(1)
}
