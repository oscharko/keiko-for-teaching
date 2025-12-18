'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { PlayCircle, Settings, Code } from 'lucide-react';

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Model settings
  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState([1000]);
  const [topP, setTopP] = useState([0.9]);
  const [model, setModel] = useState('gpt-4');

  const handleSubmit = async () => {
    setIsLoading(true);
    // TODO: Implement actual API call
    setTimeout(() => {
      setResponse('This is a placeholder response. Implement actual API integration.');
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-headline font-bold mb-2">AI Playground</h1>
        <p className="text-muted-foreground">
          Experiment with AI models and fine-tune parameters
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Model Selector */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              {/* Temperature */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Temperature</label>
                  <span className="text-sm text-muted-foreground">{temperature[0]}</span>
                </div>
                <Slider
                  value={temperature}
                  onValueChange={setTemperature}
                  min={0}
                  max={2}
                  step={0.1}
                />
                <p className="text-xs text-muted-foreground">
                  Controls randomness. Lower is more focused.
                </p>
              </div>

              {/* Max Tokens */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Max Tokens</label>
                  <span className="text-sm text-muted-foreground">{maxTokens[0]}</span>
                </div>
                <Slider
                  value={maxTokens}
                  onValueChange={setMaxTokens}
                  min={100}
                  max={4000}
                  step={100}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum length of the response.
                </p>
              </div>

              {/* Top P */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Top P</label>
                  <span className="text-sm text-muted-foreground">{topP[0]}</span>
                </div>
                <Slider
                  value={topP}
                  onValueChange={setTopP}
                  min={0}
                  max={1}
                  step={0.1}
                />
                <p className="text-xs text-muted-foreground">
                  Nucleus sampling threshold.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Playground Area */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Playground
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs defaultValue="prompt">
                <TabsList className="w-full">
                  <TabsTrigger value="prompt" className="flex-1">Prompt</TabsTrigger>
                  <TabsTrigger value="response" className="flex-1">Response</TabsTrigger>
                </TabsList>
                
                <TabsContent value="prompt" className="mt-4">
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Enter your prompt here..."
                    rows={15}
                    className="font-mono"
                  />
                  <Button
                    onClick={handleSubmit}
                    disabled={isLoading || !prompt}
                    className="mt-4 bg-keiko-primary text-keiko-black hover:opacity-90"
                  >
                    <PlayCircle className="mr-2 h-4 w-4" />
                    {isLoading ? 'Generating...' : 'Run'}
                  </Button>
                </TabsContent>
                
                <TabsContent value="response" className="mt-4">
                  <div className="min-h-[400px] p-4 border rounded-md bg-muted/50 font-mono text-sm whitespace-pre-wrap">
                    {response || 'Response will appear here...'}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

