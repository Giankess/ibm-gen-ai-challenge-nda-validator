import React from 'react';
import { ThemeProvider, createTheme, CssBaseline, Container, Box, Typography } from '@mui/material';
import DocumentUpload from './components/DocumentUpload';

// Create a theme instance with Huber + Suhner colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#003366', // Huber + Suhner blue
      light: '#004d99',
      dark: '#002244',
    },
    secondary: {
      main: '#0066cc', // Lighter blue for secondary actions
      light: '#3385d6',
      dark: '#004c99',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Helvetica Neue", Arial, sans-serif',
    h1: {
      fontSize: '2.75rem',
      fontWeight: 700,
      color: '#003366',
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '2.25rem',
      fontWeight: 600,
      color: '#003366',
      letterSpacing: '-0.01em',
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 600,
      color: '#003366',
      letterSpacing: '-0.01em',
    },
    body1: {
      fontSize: '1.125rem',
      lineHeight: 1.7,
      color: '#4a5568',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          padding: '10px 24px',
          fontSize: '1rem',
          transition: 'all 0.2s ease-in-out',
        },
        contained: {
          boxShadow: '0 2px 4px rgba(0, 51, 102, 0.1)',
          '&:hover': {
            boxShadow: '0 4px 8px rgba(0, 51, 102, 0.2)',
            transform: 'translateY(-1px)',
          },
        },
        outlined: {
          borderWidth: 2,
          '&:hover': {
            borderWidth: 2,
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
        },
      },
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)',
          py: { xs: 4, md: 6 },
        }}
      >
        <Container maxWidth="lg">
          <Box 
            sx={{ 
              mb: { xs: 4, md: 6 }, 
              textAlign: 'center',
              px: { xs: 2, md: 0 },
            }}
          >
            <Typography 
              variant="h1" 
              gutterBottom
              sx={{
                background: 'linear-gradient(135deg, #003366 0%, #0066cc 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2,
              }}
            >
              NDA Validator
            </Typography>
            <Typography 
              variant="body1" 
              color="text.secondary" 
              sx={{ 
                maxWidth: 600, 
                mx: 'auto',
                opacity: 0.9,
              }}
            >
              Validate your Non-Disclosure Agreements against Huber + Sühner's requirements
            </Typography>
          </Box>
          <DocumentUpload />
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App; 