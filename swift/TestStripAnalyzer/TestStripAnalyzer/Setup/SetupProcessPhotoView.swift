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
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
        
        // disable 'done' button until an image was captured
        navigationItem.rightBarButtonItem?.isEnabled = false
        
        if let imageData = photo?.fileDataRepresentation() {
            if let previewImage = UIImage(data: imageData) {
                let detector = StripeDetection(photo: previewImage, delegate: self)
                detector.detectRectangle()
            }
        }
        
    }
    
    
    func processingFinishedDelegate(processed: UIImage!) {
        imageView.image = processed        
        navigationItem.rightBarButtonItem?.isEnabled = true
    }

}
