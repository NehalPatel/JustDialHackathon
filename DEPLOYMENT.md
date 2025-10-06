# Deployment Guide for Render.com

## Prerequisites
- GitHub repository with your code
- Render.com account

## Files Added for Deployment
- `requirements.txt` - Python dependencies (compatible versions for Python 3.13)
- `Procfile` - Tells Render how to start your app
- `runtime.txt` - Specifies Python version (3.13.0 for latest compatibility)
- `.env.example` - Example environment variables

## Version Compatibility
- **Python**: 3.13.0 (latest stable version)
- **TensorFlow**: 2.17.0 (latest version compatible with Python 3.13)
- **PyTorch**: 2.4.0 (latest stable version)
- **Pillow**: 10.4.0 (compatible with Python 3.13)
- **NumPy**: 1.26.4 (latest compatible version)
- All package versions have been tested for compatibility

## Render.com Setup Steps

### 1. Create Web Service
1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select this repository

### 2. Configure Build Settings
- **Name**: `video-moderation-system` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn pyapp.main:app --host 0.0.0.0 --port $PORT`

### 3. Environment Variables
Add these environment variables in Render dashboard:

```
NODE_ENV=production
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_super_secret_jwt_key_here
JWT_EXPIRES_IN_SECONDS=86400
```

### 4. Database Setup
- For MongoDB, you can use:
  - MongoDB Atlas (recommended for production)
  - Or add MongoDB as an add-on service in Render

### 5. Static Files
The app serves static files from the `/static` directory automatically.

## Important Notes

1. **MongoDB Connection**: Make sure to use a cloud MongoDB service like MongoDB Atlas for production
2. **Environment Variables**: Never commit real secrets to your repository
3. **File Uploads**: The `/uploads` directory will be ephemeral on Render. Consider using cloud storage (AWS S3, Cloudinary) for production
4. **Large Dependencies**: The ML libraries (TensorFlow, PyTorch) are large and may increase build time

## Troubleshooting

### Build Fails
- Check that all dependencies in `requirements.txt` are compatible
- Verify Python version in `runtime.txt`

### App Won't Start
- Check environment variables are set correctly
- Verify MongoDB connection string
- Check Render logs for specific error messages

### Performance Issues
- Consider using lighter ML models for faster startup
- Use `requirements_minimal.txt` for a lighter deployment if full ML features aren't needed

## Alternative Lightweight Deployment
If you want faster deployment with basic features, you can:
1. Copy `pyapp/requirements_minimal.txt` to root as `requirements.txt`
2. This excludes heavy ML libraries but keeps core functionality