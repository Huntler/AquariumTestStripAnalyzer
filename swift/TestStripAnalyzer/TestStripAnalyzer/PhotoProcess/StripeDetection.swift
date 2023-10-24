//
//  StripeDetection.swift
//  TestStripAnalyzer
//
//  Created by Jonas Leuchtenberger on 22.10.23.
//

import UIKit
import Foundation
import Vision
import AVFoundation


class StripeDetection {
    
    private let delegate: StripeDetectionDelegate!
    private let originalImage: UIImage!
    private let image: UIImage!
    
    private var processingFinished = false
    private var croppedImage: UIImage?
    private var rectangles: [VNRectangleObservation]?
    private var rectsImage: UIImage?
    
    init(photo: UIImage, delegate: StripeDetectionDelegate) {
        self.originalImage = photo
        self.image = StripeDetection.normalizeOrientation(image: photo)
        self.delegate = delegate
    }
    
    func hasProcessedImage() -> Bool {
        return processingFinished
    }
    
    func getProcessedImage() -> UIImage? {
        return croppedImage
    }
    
    func getDetectionImage() -> UIImage? {
        return rectsImage
    }
    
    func detectRectangle() {
        let requestHandler = VNImageRequestHandler(cgImage: StripeDetection.convertUIImageToCGImage(image: image))
        lazy var request: VNDetectRectanglesRequest = {
            let rectDetectRequest = VNDetectRectanglesRequest(completionHandler: nil)
            
            // Customize & configure the request to detect only certain rectangles.
            rectDetectRequest.maximumObservations = 10
            rectDetectRequest.minimumConfidence = 0.1
            rectDetectRequest.minimumSize = 0.0
            rectDetectRequest.quadratureTolerance = 15.0
            rectDetectRequest.minimumAspectRatio = 0.06
            rectDetectRequest.maximumAspectRatio = 0.09
            
            return rectDetectRequest
        }()
        
        // execute the request
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try requestHandler.perform([request])
                self.completedVisionRequest(request)
                
            } catch {
                print("Error: Rectangle detection failed - vision request failed.")
            }
        }
    }
    
    private func completedVisionRequest(_ request: VNRequest?) {
        // Only proceed if a rectangular image was detected.
        guard let rectangles = request?.results as? [VNRectangleObservation] else {
            print("Error: Rectangle detection failed - Vision request returned an error.")
            return
        }
        
        // do stuff with your rectangles
        self.drawRectsOnCGImage(rectangles: rectangles)
        DispatchQueue.main.async {
            self.delegate.processingFinishedDelegate(detection: self)
        }
        
        processingFinished = true
    }
    
    private static func normalizeOrientation(image: UIImage) -> UIImage {
        guard let cgImage = image.cgImage else { return image}
        return UIImage(cgImage: cgImage, scale: image.scale, orientation: .up)
    }
    
    private func resetOrientation(image: UIImage) -> UIImage {
        guard let cgImage = image.cgImage else { return image}
        return UIImage(cgImage: cgImage, scale: image.scale, orientation: self.originalImage.imageOrientation)
    }
    
    private func extractStripe(image: UIImage, rect: CGRect) -> CGImage? {
        guard let cgImage = image.cgImage else { return nil}
        
        print(rect.minX, rect.maxX, rect.minY, rect.maxY)
        
        let minX = rect.minX * CGFloat(cgImage.width)
        let maxX = rect.maxX * CGFloat(cgImage.width)
        let minY = CGFloat(cgImage.height) - rect.minY * CGFloat(cgImage.height)
        let maxY = CGFloat(cgImage.height) - rect.maxY * CGFloat(cgImage.height)
        
        let width = maxX - minX
        let height = maxY - minY
        
        let croppedRect = CGRect(x: minX, y: minY, width: width, height: height)
        return image.cgImage?.cropping(to: croppedRect)
    }
    
    private func drawRectsOnCGImage(rectangles: [VNRectangleObservation]) {
        self.rectangles = rectangles
        if rectangles.count == 0 {
            // send to delegate, no result
            return
        }
        
        // cropping image to size of rectangle TODO: need sorting based on confidence
        if let cropped = extractStripe(image: self.image, rect: rectangles[0].boundingBox) {
            croppedImage = resetOrientation(image: UIImage(cgImage: cropped))
        }
        
        // initialize image drawing context
        let imageSize = self.image.size
        UIGraphicsBeginImageContextWithOptions(imageSize, false, self.image.scale)
        self.image.draw(at: CGPoint.zero)
        
        guard let context = UIGraphicsGetCurrentContext() else {
            return
        }
        
        context.setLineWidth(10.0)
        context.setStrokeColor(UIColor.red.cgColor)
        
        // draw each rectangle
        print("Amount of rectangles: ", rectangles.count)
        for rectangle in rectangles {
            let size = (rectangle.boundingBox.height + rectangle.boundingBox.width) / 2
            print("confidence=", rectangle.confidence,
                  ", ratio=", rectangle.boundingBox.height / rectangle.boundingBox.width,
                  ", size=", size)
            
            // swap X -> Y and Y -> X
            let minX = rectangle.boundingBox.minX * imageSize.width
            let maxX = rectangle.boundingBox.maxX * imageSize.width
            let minY = imageSize.height - rectangle.boundingBox.minY * imageSize.height
            let maxY = imageSize.height - rectangle.boundingBox.maxY * imageSize.height
            
            // draw the rectangle as lines
            let corner1 = CGPoint(x: minX, y: minY)
            context.move(to: corner1)
            
            let corner2 = CGPoint(x: minX, y: maxY)
            context.addLine(to: corner2)
            
            let corner3 = CGPoint(x: maxX, y: maxY)
            context.addLine(to: corner3)
            
            let corner4 = CGPoint(x: maxX, y: minY)
            context.addLine(to: corner4)
            context.addLine(to: corner1)
            
            context.strokePath()
        }
        
        // end the drawing context
        if let newImage = UIGraphicsGetImageFromCurrentImageContext() {
            rectsImage = resetOrientation(image: newImage)
        }
        UIGraphicsEndImageContext()
    }
    
    static func captureToUIImage(photo: AVCapturePhoto?) -> UIImage! {
        if let imageData = photo?.fileDataRepresentation() {
            if let uiImage = UIImage(data: imageData) {
                return uiImage
            }
        }
        
        return nil
    }
    
    static func convertUIImageToCGImage(image: UIImage) -> CGImage! {
        return image.cgImage
    }
}

protocol StripeDetectionDelegate {
    func processingFinishedDelegate(detection: StripeDetection)
}
