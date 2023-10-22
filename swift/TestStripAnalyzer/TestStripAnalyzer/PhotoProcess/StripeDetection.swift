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
    
    let delegate: StripeDetectionDelegate
    let photo: UIImage!
    
    init(photo: UIImage, delegate: StripeDetectionDelegate) {
        self.photo = photo
        self.delegate = delegate
    }
    
    func detectRectangle() {
        let requestHandler = VNImageRequestHandler(cgImage: StripeDetection.convertUIImageToCGImage(image: photo))
        lazy var request: VNDetectRectanglesRequest = {
            let rectDetectRequest = VNDetectRectanglesRequest(completionHandler: nil)
            
            // Customize & configure the request to detect only certain rectangles.
            rectDetectRequest.maximumObservations = 5
            rectDetectRequest.minimumConfidence = 0.5
            rectDetectRequest.minimumSize = 0.08
            rectDetectRequest.quadratureTolerance = 15.0
            rectDetectRequest.minimumAspectRatio = 0.04
            rectDetectRequest.maximumAspectRatio = 0.2
            
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
    
    func completedVisionRequest(_ request: VNRequest?) {
        // Only proceed if a rectangular image was detected.
        guard let rectangles = request?.results as? [VNRectangleObservation] else {
            print("Error: Rectangle detection failed - Vision request returned an error.")
            return
        }
        
        // do stuff with your rectangles
        self.drawRectsOnCGImage(rectangles: rectangles)
    }
    
    func drawRectsOnCGImage(rectangles: [VNRectangleObservation]) {
        if rectangles.count == 0 {
            // send to delegate, no result
            DispatchQueue.main.async {
                self.delegate.processingFinishedDelegate(processed: self.photo)
            }
            return
        }
        
        // initialize image drawing context
        let imageSize = self.photo.size
        let scale: CGFloat = 0
        UIGraphicsBeginImageContextWithOptions(imageSize, false, scale)
        self.photo.draw(at: CGPoint.zero)
        
        guard let context = UIGraphicsGetCurrentContext() else {
            self.delegate.processingFinishedDelegate(processed: self.photo)
            return
        }
        
        context.setLineWidth(10.0)
        context.setStrokeColor(UIColor.red.cgColor)
        
        // draw each rectangle
        print("Amount of rectangles: ", rectangles.count)
        for rectangle in rectangles {
            print(rectangle.confidence)
            
            // swap X -> Y and Y -> X
            let minX = rectangle.boundingBox.minY * imageSize.width
            let maxX = rectangle.boundingBox.maxY * imageSize.width
            let minY = rectangle.boundingBox.minX * imageSize.height
            let maxY = rectangle.boundingBox.maxX * imageSize.height
            
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
        let newImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        // send to delegate
        DispatchQueue.main.async {
            self.delegate.processingFinishedDelegate(processed: newImage)
        }
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
        if let ciImage = CIImage(image: image) {
            let context = CIContext(options: nil)
            return context.createCGImage(ciImage, from: ciImage.extent)
        }
        
        return nil
    }
}

protocol StripeDetectionDelegate {
    func processingFinishedDelegate(processed: UIImage!)
}
