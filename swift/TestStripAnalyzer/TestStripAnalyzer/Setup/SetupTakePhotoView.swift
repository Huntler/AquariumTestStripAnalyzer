//
//  ViewController.swift
//  TestStripAnalyzer
//
//  Created by Jonas Leuchtenberger on 19.10.23.
//

import UIKit
import AVFoundation


class SetupTakePhotoView: UIViewController, AVCapturePhotoCaptureDelegate {
    
    @IBOutlet var captureButton: UIButton!
    @IBOutlet var imageView: UIImageView!
    
    var captureSession: AVCaptureSession!
    var previewLayer: AVCaptureVideoPreviewLayer!
    var photoOutput: AVCapturePhotoOutput!
    var photo: AVCapturePhoto!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
        
        // disable 'continue' button until an image was captured
        navigationItem.rightBarButtonItem?.isEnabled = false
        
        // initialize the photo output
        photoOutput = AVCapturePhotoOutput()
        
        openCamera()
        setupCaptureSession()
    }
    
    func openCamera() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            self.setupCaptureSession()
            
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { (granted) in
                if granted {
                    DispatchQueue.main.async {
                        self.setupCaptureSession()
                    }
                }
                else {
                    self.handleDismiss()
                }
            }
        default:
            self.handleDismiss()
        }
    }
    
    func setupCaptureSession() {
        captureSession = AVCaptureSession()
        
        if let captureDevice = AVCaptureDevice.default(for: AVMediaType.video) {
            do {
                let input = try AVCaptureDeviceInput(device: captureDevice)
                if captureSession.canAddInput(input) {
                    captureSession.addInput(input)
                }
            } catch let error {
                print("Failed to set input device with error: \(error)")
            }
            
            if captureSession.canAddOutput(photoOutput) {
                captureSession.addOutput(photoOutput)
            }
            
            // preview layer to display the camera feed
            previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
            previewLayer.videoGravity = .resizeAspectFill
            previewLayer.frame = imageView.bounds
            imageView.layer.addSublayer(previewLayer)
            
            captureSession.sessionPreset = .photo
            
            // start the capture session async to prevent UI blocking
            DispatchQueue.global().async {
                self.captureSession.startRunning()
            }
        }
    }

    @IBAction func capturePhoto() {
        captureSession.stopRunning()
        
        // define photo settings
        let photoSettings = AVCapturePhotoSettings()
        photoSettings.flashMode = .on
        photoSettings.photoQualityPrioritization = .speed
        if let photoPreviewType = photoSettings.availablePreviewPhotoPixelFormatTypes.first {
            photoSettings.previewPhotoFormat = [kCVPixelBufferPixelFormatTypeKey as String: photoPreviewType]
        }
        
        // take a photo and delegate to 'photoOutput'
        photoOutput.capturePhoto(with: photoSettings, delegate: self)
        captureButton.isEnabled = false
    }
    
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        // stop capturing
        captureSession.removeOutput(photoOutput)
        captureSession.stopRunning()
        imageView.layer.sublayers?.removeAll()
        
        // get the image
        guard let imageData = photo.fileDataRepresentation() else { return }
        let previewImage = UIImage(data: imageData)
        imageView.image = previewImage
        
        self.photo = photo
        
        // enable the 'continue' button
        navigationItem.rightBarButtonItem?.isEnabled = true
    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if let processView = segue.destination as? SetupProcessPhotoView {
            processView.photo = photo
        }
    }
    
    func handleDismiss() {
        
    }
}
