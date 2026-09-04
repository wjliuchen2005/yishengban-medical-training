import AppKit
import CoreImage
import Foundation

guard CommandLine.arguments.count == 3 else {
    fputs("Usage: swift generate_qr.swift <text> <output.png>\n", stderr)
    exit(2)
}

let text = CommandLine.arguments[1]
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])

guard
    let filter = CIFilter(name: "CIQRCodeGenerator"),
    let correction = CIFilter(name: "CIFalseColor")
else {
    fputs("Unable to create QR filters.\n", stderr)
    exit(1)
}

filter.setValue(Data(text.utf8), forKey: "inputMessage")
filter.setValue("M", forKey: "inputCorrectionLevel")

guard let qrImage = filter.outputImage else {
    fputs("Unable to generate QR image.\n", stderr)
    exit(1)
}

correction.setValue(qrImage, forKey: kCIInputImageKey)
correction.setValue(CIColor.black, forKey: "inputColor0")
correction.setValue(CIColor.white, forKey: "inputColor1")

guard let coloredImage = correction.outputImage else {
    fputs("Unable to color QR image.\n", stderr)
    exit(1)
}

let scaledImage = coloredImage.transformed(by: CGAffineTransform(scaleX: 12, y: 12))
let representation = NSCIImageRep(ciImage: scaledImage)
let image = NSImage(size: representation.size)
image.addRepresentation(representation)

guard
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let png = bitmap.representation(using: .png, properties: [:])
else {
    fputs("Unable to encode PNG.\n", stderr)
    exit(1)
}

try png.write(to: outputURL, options: .atomic)
print(outputURL.path)

