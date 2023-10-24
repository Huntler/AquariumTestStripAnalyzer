//
//  SetupChangeBoxView.swift
//  TestStripAnalyzer
//
//  Created by Jonas Leuchtenberger on 23.10.23.
//

import UIKit

class SetupChangeBoxView: UIViewController {
    
    @IBOutlet var imageView: UIImageView!
    var detector: StripeDetection?

    override func viewDidLoad() {
        super.viewDidLoad()

        imageView.image = detector?.getDetectionImage()
    }

}
