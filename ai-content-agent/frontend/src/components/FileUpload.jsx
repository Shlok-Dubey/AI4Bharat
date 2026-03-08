import { useState } from 'react'
import '../styles/FileUpload.css'

function FileUpload({ onFilesSelected, maxFiles = 5 }) {
    const [selectedFiles, setSelectedFiles] = useState([])
    const [previews, setPreviews] = useState([])

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files)

        if (files.length + selectedFiles.length > maxFiles) {
            alert(`You can only upload up to ${maxFiles} files`)
            return
        }

        // Validate file types
        const validFiles = files.filter(file => {
            const isImage = file.type.startsWith('image/')
            const isVideo = file.type.startsWith('video/')
            return isImage || isVideo
        })

        if (validFiles.length !== files.length) {
            alert('Only image and video files are allowed')
        }

        // Create previews
        const newPreviews = validFiles.map(file => ({
            file,
            url: URL.createObjectURL(file),
            type: file.type.startsWith('image/') ? 'image' : 'video',
            name: file.name,
            size: (file.size / (1024 * 1024)).toFixed(2) // MB
        }))

        const updatedFiles = [...selectedFiles, ...validFiles]
        const updatedPreviews = [...previews, ...newPreviews]

        setSelectedFiles(updatedFiles)
        setPreviews(updatedPreviews)

        if (onFilesSelected) {
            onFilesSelected(updatedFiles)
        }
    }

    const removeFile = (index) => {
        const newFiles = selectedFiles.filter((_, i) => i !== index)
        const newPreviews = previews.filter((_, i) => i !== index)

        // Revoke object URL to free memory
        URL.revokeObjectURL(previews[index].url)

        setSelectedFiles(newFiles)
        setPreviews(newPreviews)

        if (onFilesSelected) {
            onFilesSelected(newFiles)
        }
    }

    return (
        <div className="file-upload-container">
            <div className="upload-area">
                <input
                    type="file"
                    id="file-input"
                    multiple
                    accept="image/*,video/*"
                    onChange={handleFileChange}
                    className="file-input"
                />
                <label htmlFor="file-input" className="upload-label">
                    <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span className="upload-text">
                        Click to upload or drag and drop
                    </span>
                    <span className="upload-hint">
                        Images or videos (max {maxFiles} files, 100MB each)
                    </span>
                </label>
            </div>

            {previews.length > 0 && (
                <div className="preview-grid">
                    {previews.map((preview, index) => (
                        <div key={index} className="preview-item">
                            <button
                                type="button"
                                onClick={() => removeFile(index)}
                                className="remove-btn"
                            >
                                ×
                            </button>
                            {preview.type === 'image' ? (
                                <img src={preview.url} alt={preview.name} className="preview-media" />
                            ) : (
                                <video src={preview.url} className="preview-media" controls />
                            )}
                            <div className="preview-info">
                                <div className="preview-name">{preview.name}</div>
                                <div className="preview-size">{preview.size} MB</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default FileUpload


