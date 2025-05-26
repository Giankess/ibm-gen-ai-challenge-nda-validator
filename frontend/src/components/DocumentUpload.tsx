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
  Fade,
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
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
      <Paper
        {...getRootProps()}
        sx={{
          p: { xs: 4, md: 6 },
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 24px rgba(0, 51, 102, 0.12)',
          },
        }}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CircularProgress 
              size={40} 
              sx={{
                color: 'primary.main',
                filter: 'drop-shadow(0 2px 4px rgba(0, 51, 102, 0.1))',
              }}
            />
            <Typography variant="body1" color="text.secondary">
              Uploading document...
            </Typography>
          </Box>
        ) : (
          <>
            <CloudUploadIcon 
              sx={{ 
                fontSize: { xs: 48, md: 64 }, 
                color: 'primary.main', 
                mb: 3,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: isDragActive ? 'scale(1.1) translateY(-4px)' : 'scale(1)',
                filter: isDragActive ? 'drop-shadow(0 4px 8px rgba(0, 51, 102, 0.2))' : 'none',
              }} 
            />
            <Typography 
              variant="h4" 
              gutterBottom
              sx={{
                transition: 'all 0.3s ease',
                transform: isDragActive ? 'translateY(-4px)' : 'none',
              }}
            >
              {isDragActive ? 'Drop your document here' : 'Upload your NDA'}
            </Typography>
            <Typography 
              variant="body1" 
              color="text.secondary"
              sx={{
                transition: 'all 0.3s ease',
                transform: isDragActive ? 'translateY(-4px)' : 'none',
              }}
            >
              {isDragActive
                ? 'Release to upload your document'
                : 'Drag and drop a Word document here, or click to select'}
            </Typography>
          </>
        )}
      </Paper>

      <Fade in={!!error}>
        <Alert 
          severity="error" 
          sx={{ 
            mt: 1.5,
            borderRadius: 2,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
          }}
        >
          {error}
        </Alert>
      </Fade>

      <Fade in={!!success}>
        <Alert 
          severity="success" 
          sx={{ 
            mt: 1.5,
            borderRadius: 2,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
          }}
        >
          {success}
        </Alert>
      </Fade>

      <Fade in={documentStatus?.status === 'completed'}>
        <Stack 
          direction={{ xs: 'column', sm: 'row' }} 
          spacing={2} 
          sx={{ 
            mt: 1.5,
            justifyContent: 'center',
            '& .MuiButton-root': {
              minWidth: { xs: '100%', sm: 200 },
              height: 48,
            },
          }}
        >
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => handleDownload('redline')}
            sx={{
              bgcolor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
            }}
          >
            Download Redline Version
          </Button>
          {!documentStatus?.clean_path ? (
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleGenerateClean}
              disabled={generatingClean}
              sx={{
                borderColor: 'primary.main',
                color: 'primary.main',
                '&:hover': {
                  borderColor: 'primary.dark',
                  bgcolor: 'primary.light',
                  color: 'white',
                },
              }}
            >
              {generatingClean ? 'Generating...' : 'Generate Clean Version'}
            </Button>
          ) : (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => handleDownload('clean')}
              sx={{
                bgcolor: 'secondary.main',
                '&:hover': {
                  bgcolor: 'secondary.dark',
                },
              }}
            >
              Download Clean Version
            </Button>
          )}
        </Stack>
      </Fade>
    </Box>
  );
};

export default DocumentUpload; 