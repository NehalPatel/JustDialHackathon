import api from './api';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export const getProjects = async (): Promise<Project[]> => {
  const res = await api.get('/projects');
  return (res.data.data.projects || []).map((p: any) => ({
    id: p._id,
    name: p.name,
    description: p.description,
    status: p.status,
    createdAt: p.createdAt,
    updatedAt: p.updatedAt,
  }));
};

export const createProject = async (data: { name: string; description?: string }): Promise<Project> => {
  const res = await api.post('/projects', data);
  const p = res.data.data.project;
  return {
    id: p._id,
    name: p.name,
    description: p.description,
    status: p.status,
    createdAt: p.createdAt,
    updatedAt: p.updatedAt,
  };
};