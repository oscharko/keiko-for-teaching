export type IdeaStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'implemented';

export type RecommendationClass =
  | 'quick_win'
  | 'high_leverage'
  | 'strategic'
  | 'evaluate';

export interface Idea {
  ideaId: string;
  title: string;
  description: string;
  problemDescription?: string;
  expectedBenefit?: string;
  status: IdeaStatus;
  submitterId: string;
  submitterName?: string;
  department?: string;
  createdAt: number;
  updatedAt: number;
  impactScore?: number;
  feasibilityScore?: number;
  recommendationClass?: RecommendationClass;
  tags?: string[];
}

export interface IdeaSubmission {
  title: string;
  description: string;
  problemDescription?: string;
  expectedBenefit?: string;
  department?: string;
}

export interface SimilarIdea {
  ideaId: string;
  title: string;
  summary: string;
  similarityScore: number;
  status: IdeaStatus;
}

export interface SimilarIdeasResponse {
  similarIdeas: SimilarIdea[];
  threshold: number;
}

