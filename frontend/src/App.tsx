import React from 'react';
import { ThemeProvider, createTheme, CssBaseline, Container, Box } from '@mui/material';
import DocumentUpload from './components/DocumentUpload';

// Create a theme instance with Huber + Suhner colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#003366', // Huber + Suhner blue
    },
    secondary: {
      main: '#FF0000', // Huber + Suhner red
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Helvetica Neue", Arial, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <DocumentUpload />
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App; 