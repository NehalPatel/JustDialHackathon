import { useEffect, useState } from 'react';
import { Box, Button, Card, CardContent, Grid, TextField, Typography } from '@mui/material';
import { createProject, getProjects, Project } from '../services/projects';

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      const created = await createProject({ name: name.trim(), description });
      setProjects((prev) => [created, ...prev]);
      setName('');
      setDescription('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Projects
      </Typography>
      <Box component="form" onSubmit={handleCreate} sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <TextField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <Button type="submit" variant="contained" disabled={loading}>Create</Button>
      </Box>
      <Grid container spacing={2}>
        {projects.map((p) => (
          <Grid item xs={12} md={6} lg={4} key={p.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{p.name}</Typography>
                {p.description && (
                  <Typography variant="body2" color="text.secondary">{p.description}</Typography>
                )}
                <Typography variant="caption" color="text.secondary">Status: {p.status}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      {projects.length === 0 && !loading && (
        <Typography color="text.secondary">No projects yet. Create one above.</Typography>
      )}
    </Box>
  );
}