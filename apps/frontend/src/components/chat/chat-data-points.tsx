'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart3, TrendingUp, Database } from 'lucide-react';

export interface DataPoint {
  label: string;
  value: string | number;
  type?: 'metric' | 'stat' | 'fact';
  unit?: string;
}

interface ChatDataPointsProps {
  dataPoints: DataPoint[];
}

export function ChatDataPoints({ dataPoints }: ChatDataPointsProps) {
  if (!dataPoints || dataPoints.length === 0) {
    return null;
  }

  const getIcon = (type?: string) => {
    switch (type) {
      case 'metric':
        return <BarChart3 className="h-4 w-4" />;
      case 'stat':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <Database className="h-4 w-4" />;
    }
  };

  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
        <Database className="h-4 w-4" />
        Key Data Points
      </h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {dataPoints.map((point, index) => (
          <Card key={index} className="bg-muted/50">
            <CardContent className="p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">
                    {point.label}
                  </p>
                  <p className="text-lg font-mono font-semibold">
                    {point.value}
                    {point.unit && (
                      <span className="text-sm text-muted-foreground ml-1">
                        {point.unit}
                      </span>
                    )}
                  </p>
                </div>
                <div className="text-muted-foreground">
                  {getIcon(point.type)}
                </div>
              </div>
              {point.type && (
                <Badge variant="outline" className="mt-2 text-xs">
                  {point.type}
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

