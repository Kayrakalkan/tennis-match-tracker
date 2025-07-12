// Image cropping functionality
class ImageCropper {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.image = null;
        this.cropArea = null;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.tempFilename = null;
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        const photoInput = document.getElementById('photo');
        if (photoInput) {
            photoInput.addEventListener('change', (e) => this.handleImageSelect(e));
        }
        
        const detectFacesBtn = document.getElementById('detect-faces-btn');
        if (detectFacesBtn) {
            detectFacesBtn.addEventListener('click', () => this.detectFaces());
        }
        
        const resetCropBtn = document.getElementById('reset-crop-btn');
        if (resetCropBtn) {
            resetCropBtn.addEventListener('click', () => this.resetCrop());
        }
        
        // Form submission
        const form = document.getElementById('add-player-form') || document.getElementById('edit-player-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    }
    
    handleImageSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (JPEG, PNG, GIF)');
            return;
        }
        
        // Show crop container
        const cropContainer = document.getElementById('crop-container');
        cropContainer.style.display = 'block';
        
        // Initialize canvas
        this.canvas = document.getElementById('crop-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Load image
        const reader = new FileReader();
        reader.onload = (e) => {
            this.image = new Image();
            this.image.onload = () => {
                this.setupCanvas();
                this.drawImage();
                this.setupCropEvents();
            };
            this.image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    setupCanvas() {
        const maxWidth = 500;
        const maxHeight = 400;
        
        let { width, height } = this.image;
        
        // Scale image to fit canvas
        if (width > maxWidth || height > maxHeight) {
            const ratio = Math.min(maxWidth / width, maxHeight / height);
            width *= ratio;
            height *= ratio;
        }
        
        this.canvas.width = width;
        this.canvas.height = height;
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
        
        // Store scale factor for crop calculations
        this.scaleX = this.image.width / width;
        this.scaleY = this.image.height / height;
    }
    
    drawImage() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.image, 0, 0, this.canvas.width, this.canvas.height);
        
        // Draw crop area if exists
        if (this.cropArea) {
            this.drawCropArea();
        }
    }
    
    drawCropArea() {
        if (!this.cropArea) return;
        
        const { x, y, width, height } = this.cropArea;
        
        // Draw overlay
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Clear crop area
        this.ctx.clearRect(x, y, width, height);
        this.ctx.drawImage(this.image, 
            x * this.scaleX, y * this.scaleY, width * this.scaleX, height * this.scaleY,
            x, y, width, height);
        
        // Draw border
        this.ctx.strokeStyle = '#4a7c59';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x, y, width, height);
        
        // Draw corner handles
        this.drawHandle(x - 5, y - 5);
        this.drawHandle(x + width - 5, y - 5);
        this.drawHandle(x - 5, y + height - 5);
        this.drawHandle(x + width - 5, y + height - 5);
    }
    
    drawHandle(x, y) {
        this.ctx.fillStyle = '#4a7c59';
        this.ctx.fillRect(x, y, 10, 10);
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(x, y, 10, 10);
    }
    
    setupCropEvents() {
        this.canvas.addEventListener('mousedown', (e) => this.startCrop(e));
        this.canvas.addEventListener('mousemove', (e) => this.updateCrop(e));
        this.canvas.addEventListener('mouseup', () => this.endCrop());
        this.canvas.addEventListener('mouseleave', () => this.endCrop());
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.startCrop(e.touches[0]));
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.updateCrop(e.touches[0]);
        });
        this.canvas.addEventListener('touchend', () => this.endCrop());
    }
    
    startCrop(e) {
        const rect = this.canvas.getBoundingClientRect();
        this.startX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        this.startY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        this.isDragging = true;
        
        this.cropArea = {
            x: this.startX,
            y: this.startY,
            width: 0,
            height: 0
        };
    }
    
    updateCrop(e) {
        if (!this.isDragging) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const currentY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        
        // Calculate crop area
        const width = Math.abs(currentX - this.startX);
        const height = Math.abs(currentY - this.startY);
        
        // Make it square
        const size = Math.min(width, height);
        
        this.cropArea = {
            x: Math.min(this.startX, currentX),
            y: Math.min(this.startY, currentY),
            width: size,
            height: size
        };
        
        // Ensure crop area stays within canvas bounds
        if (this.cropArea.x + this.cropArea.width > this.canvas.width) {
            this.cropArea.x = this.canvas.width - this.cropArea.width;
        }
        if (this.cropArea.y + this.cropArea.height > this.canvas.height) {
            this.cropArea.y = this.canvas.height - this.cropArea.height;
        }
        
        this.drawImage();
    }
    
    endCrop() {
        this.isDragging = false;
    }
    
    async detectFaces() {
        if (!this.tempFilename) {
            alert('Please upload an image first');
            return;
        }
        
        try {
            const response = await fetch(`/detect_faces/${this.tempFilename}`);
            const data = await response.json();
            
            if (data.success && data.faces.length > 0) {
                // Use the first detected face
                const face = data.faces[0];
                
                // Convert to canvas coordinates
                this.cropArea = {
                    x: face.x / this.scaleX,
                    y: face.y / this.scaleY,
                    width: face.width / this.scaleX,
                    height: face.height / this.scaleY
                };
                
                this.drawImage();
            } else {
                alert('No faces detected in the image. Try manual cropping.');
            }
        } catch (error) {
            console.error('Face detection failed:', error);
            alert('Face detection failed. Try manual cropping.');
        }
    }
    
    resetCrop() {
        this.cropArea = null;
        this.drawImage();
    }
    
    handleFormSubmit(e) {
        if (this.cropArea && this.image) {
            // Convert crop area to original image coordinates
            const cropData = {
                x: Math.round(this.cropArea.x * this.scaleX),
                y: Math.round(this.cropArea.y * this.scaleY),
                width: Math.round(this.cropArea.width * this.scaleX),
                height: Math.round(this.cropArea.height * this.scaleY)
            };
            
            // Set crop data in hidden field
            const cropDataField = document.getElementById('crop-data');
            if (cropDataField) {
                cropDataField.value = JSON.stringify(cropData);
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ImageCropper();
});
