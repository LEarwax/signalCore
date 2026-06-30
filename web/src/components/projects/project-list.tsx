"use client";

import { useState } from "react";
import Link from "next/link";
import type { Project } from "@/types";
import { NewProjectModal } from "./new-project-modal";

interface Props {
  projects: Project[];
}

export function ProjectList({ projects }: Props) {
  const [showModal, setShowModal] = useState(false);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 text-sm font-medium bg-orange-600 text-white rounded-md hover:bg-orange-700"
        >
          + New project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-2">No projects yet</p>
          <p className="text-sm">Create your first project to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="block bg-gray-900 rounded-lg border border-gray-800 p-5 hover:border-orange-500/50 hover:bg-gray-800 transition"
            >
              <h3 className="font-medium text-gray-100 mb-1 truncate">{project.name}</h3>
              {project.address && (
                <p className="text-sm text-gray-400 truncate">{project.address}</p>
              )}
              <p className="text-xs text-gray-600 mt-3">
                {new Date(project.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}

      {showModal && <NewProjectModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
