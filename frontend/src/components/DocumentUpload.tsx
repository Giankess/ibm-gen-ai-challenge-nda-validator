import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Button,
  Alert,
  Stack,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DownloadIcon from '@mui/icons-material/Download';
import EditIcon from '@mui/icons-material/Edit';
import axios from 'axios';

interface DocumentStatus {
  status: string;
  analysis: any;
  redline_path: string | null;
  clean_path: string | null;
}

const DocumentUpload: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [documentStatus, setDocumentStatus] = useState<DocumentStatus | null>(null);
  const [generatingClean, setGeneratingClean] = useState(false);

  const checkDocumentStatus = useCallback(async (filename: string) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/documents/status/${filename}`);
      setDocumentStatus(response.data);
      
      if (response.data.status === 'completed') {
        setSuccess('Document processed successfully! You can now download the redline version.');
      } else if (response.data.status === 'error') {
        setError(`Error processing document: ${response.data.error}`);
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Check if file is a Word document
    if (!file.name.match(/\.(doc|docx)$/)) {
      setError('Please upload a Word document (.doc or .docx)');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setUploadedFilename(null);
    setDocumentStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadedFilename(response.data.filename);
      setSuccess('Document uploaded successfully! Processing...');
      
      // Start polling for status
      const pollInterval = setInterval(async () => {
        await checkDocumentStatus(response.data.filename);
        if (documentStatus?.status === 'completed') {
          clearInterval(pollInterval);
        }
      }, 2000);
    } catch (err) {
      setError('Error uploading document. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  }, [checkDocumentStatus, documentStatus]);

  const handleDownload = async (version: 'redline' | 'clean') => {
    if (!uploadedFilename) return;

    try {
      const response = await axios.get(
        `http://localhost:5000/api/documents/download/${uploadedFilename}?version=${version}`,
        { responseType: 'blob' }
      );

      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${version}_${uploadedFilename}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(`Error downloading ${version} version. Please try again.`);
      console.error('Download error:', err);
    }
  };

  const handleGenerateClean = async () => {
    if (!uploadedFilename) return;

    setGeneratingClean(true);
    try {
      await axios.post(`http://localhost:5000/api/documents/generate-clean/${uploadedFilename}`);
      await checkDocumentStatus(uploadedFilename);
      setSuccess('Clean version generated successfully!');
    } catch (err) {
      setError('Error generating clean version. Please try again.');
      console.error('Generate clean error:', err);
    } finally {
      setGeneratingClean(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
  });

  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', textAlign: 'center' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        NDA Validator
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload your NDA document for validation
      </Typography>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          mt: 2,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="body1">
          {isDragActive
            ? 'Drop the document here'
            : 'Drag and drop a Word document here, or click to select'}
        </Typography>
      </Paper>

      {uploading && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {success}
        </Alert>
      )}

      {documentStatus?.status === 'completed' && (
        <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: 'center' }}>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => handleDownload('redline')}
          >
            Download Redline Version
          </Button>
          {!documentStatus.clean_path ? (
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleGenerateClean}
              disabled={generatingClean}
            >
              {generatingClean ? 'Generating...' : 'Generate Clean Version'}
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => handleDownload('clean')}
            >
              Download Clean Version
            </Button>
          )}
        </Stack>
      )}
    </Box>
  );
};

export default DocumentUpload; 