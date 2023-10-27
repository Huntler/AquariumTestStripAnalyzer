//
//  SetupReferenceColorView.swift
//  TestStripAnalyzer
//
//  Created by Jonas Leuchtenberger on 27.10.23.
//

import UIKit
import AVFoundation

class SetupReferenceColorView: UIViewController, WhiteBalanceDelegate, ColorDelegate {
    
    // Views
    @IBOutlet var cameraView: UIImageView!
    @IBOutlet var colorView: UIImageView!
    
    @IBOutlet var balanceButton: UIButton!
    
    // Class related
    var colors: [CGColor]!
    var balance: CGColor!
    
    // Camera related
    var captureSession: AVCaptureSession!
    var previewLayer: AVCaptureVideoPreviewLayer!
    var photoOutput: AVCapturePhotoOutput!
    var photo: AVCapturePhoto!

    var whiteBalanceHandler: WhiteBalanceHandler!
    var colorHandler: ColorHandler!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // initialize the colors array
        self.colors = []
        
        // initialize the capture handlers
        self.whiteBalanceHandler = WhiteBalanceHandler(delegate: self)
        self.colorHandler = ColorHandler(delegate: self)
        
        // initialize the photo output
        self.photoOutput = AVCapturePhotoOutput()
        
        self.openCamera()
        self.setupCaptureSession()
    }
    
    func whiteBalanceCaptured(color: CGColor) {
        self.balance = color
    }
    
    func colorCaptured(color: CGColor) {
        self.colors.append(color)
    }
    
    func openCamera() {
        DispatchQueue.main.async {
            self.setupCaptureSession()
        }
    }
    
    func setupCaptureSession() {
        self.captureSession = AVCaptureSession()
        
        if let captureDevice = AVCaptureDevice.default(for: AVMediaType.video) {
            do {
                let input = try AVCaptureDeviceInput(device: captureDevice)
                if self.captureSession.canAddInput(input) {
                    self.captureSession.addInput(input)
                }
            } catch let error {
                print("Failed to set input device with error: \(error)")
            }
            
            if self.captureSession.canAddOutput(self.photoOutput) {
                self.captureSession.addOutput(self.photoOutput)
            }
            
            // preview layer to display the camera feed
            self.previewLayer = AVCaptureVideoPreviewLayer(session: self.captureSession)
            self.previewLayer.videoGravity = .resizeAspectFill
            self.previewLayer.frame = self.cameraView.bounds
            self.cameraView.layer.addSublayer(self.previewLayer)
            
            // layer showing the crossair
            // TODO
            
            self.captureSession.sessionPreset = .photo
            
            // start the capture session async to prevent UI blocking
            DispatchQueue.global().async {
                self.captureSession.startRunning()
            }
        }
    }
    
    @IBAction func captureWhiteBalance() {
        
    }
    
    @IBAction func captureColor() {
        self.captureSession.stopRunning()
        
        // define photo settings
        let photoSettings = AVCapturePhotoSettings()
        photoSettings.flashMode = .off
        photoSettings.photoQualityPrioritization = .speed
        if let photoPreviewType = photoSettings.availablePreviewPhotoPixelFormatTypes.first {
            photoSettings.previewPhotoFormat = [kCVPixelBufferPixelFormatTypeKey as String: photoPreviewType]
        }
        
        // take a photo and delegate to 'photoOutput'
        self.photoOutput.capturePhoto(with: photoSettings, delegate: self.colorHandler)
        self.captureSession.startRunning()
    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        // TODO fix destination and send list of colors
        if let processView = segue.destination as? SetupProcessPhotoView {
            processView.photo = photo
        }
    }
}

protocol WhiteBalanceDelegate {
    func whiteBalanceCaptured(color: CGColor)
}

class WhiteBalanceHandler: NSObject, AVCapturePhotoCaptureDelegate {
    
    let delegate: WhiteBalanceDelegate
    
    init(delegate: WhiteBalanceDelegate) {
        self.delegate = delegate
    }
    
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        // get the image
        guard let imageData = photo.fileDataRepresentation() else { return }
        let previewImage = UIImage(data: imageData)
        
        // get color around crossair and add to colors list
        // TODO
        
        self.delegate.whiteBalanceCaptured(color: CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    }
}

protocol ColorDelegate {
    func colorCaptured(color: CGColor)
}

class ColorHandler: NSObject, AVCapturePhotoCaptureDelegate {
    
    let delegate: ColorDelegate
    
    init(delegate: ColorDelegate) {
        self.delegate = delegate
    }
    
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        // get the image
        guard let imageData = photo.fileDataRepresentation() else { return }
        let previewImage = UIImage(data: imageData)
        
        // get color around crossair and add to colors list
        // TODO
        
        self.delegate.colorCaptured(color: CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    }
}
