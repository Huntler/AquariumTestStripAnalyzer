//
//  ViewController.swift
//  TestStripAnalyzer
//
//  Created by Jonas Leuchtenberger on 19.10.23.
//

import UIKit
import AVFoundation
import Vision

class SetupProcessPhotoView: UIViewController, StripeDetectionDelegate {
    
    @IBOutlet var imageView: UIImageView!
    var photo: AVCapturePhoto?
    
    var detector: StripeDetection?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
        
        // check if the processing was already done
        var processingNeeded = true
        if let processingFinished = detector?.hasProcessedImage() {
            processingNeeded = !processingFinished
            navigationItem.rightBarButtonItem?.isEnabled = processingFinished
        }
        
        // if the processing was not executed, do so
        if processingNeeded {
            navigationItem.rightBarButtonItem?.isEnabled = false
            
            if let imageData = photo?.fileDataRepresentation() {
                if let previewImage = UIImage(data: imageData) {
                    detector = StripeDetection(photo: previewImage, delegate: self)
                    detector?.detectRectangle()
                }
            }
        }
    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if let processView = segue.destination as? SetupChangeBoxView {
            processView.detector = detector
        }
    }
    
    func processingFinishedDelegate(detection: StripeDetection) {
        if let image = detection.getProcessedImage() {
            imageView.image = image
            
            navigationItem.rightBarButtonItem?.isEnabled = true
        }
    }

}
