import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ToggleSwitch from './ToggleSwitch';
import SliderControl from './SliderControl';
import { Button } from '@/components/ui/Button';
import { Save, AlertTriangle } from 'lucide-react';

const SettingsForm = () => {
  const [autoDefense, setAutoDefense] = useState(true);
  const [threatScoring, setThreatScoring] = useState(50);
  const [loggingLevel, setLoggingLevel] = useState('INFO'); // Using a simple state for dropdown/radio for now

  const handleSave = () => {
    console.log("Saving settings:", { autoDefense, threatScoring, loggingLevel });
    // Simulate API call
    alert("Settings saved successfully!");
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl text-primary flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2" />
          SYSTEM ORCHESTRATION SETTINGS
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-6">
        <ToggleSwitch
          id="auto-defense"
          label="Autonomous Defense Mode"
          description="Enable AI-driven automated threat response actions."
          checked={autoDefense}
          onCheckedChange={setAutoDefense}
        />
        
        <SliderControl
          id="threat-scoring"
          label="Threat Scoring Sensitivity"
          description="Adjust the threshold for AI threat detection and alert generation."
          value={threatScoring}
          onValueChange={setThreatScoring}
          min={0}
          max={100}
          step={5}
        />

        {/* Placeholder for Logging Level - could be a dropdown or radio group */}
        <div className="flex flex-col gap-2 p-4 bg-panel-solid/50 border border-border rounded-lg">
            <label htmlFor="logging-level" className="text-text-primary text-md font-medium">Logging Level</label>
            <p className="text-sm text-text-secondary">Set the verbosity of system logs.</p>
            <select
                id="logging-level"
                value={loggingLevel}
                onChange={(e) => setLoggingLevel(e.target.value)}
                className="bg-background border border-border rounded-md text-text-primary text-sm p-2 focus:ring-primary focus:border-primary"
            >
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
            </select>
        </div>

        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="mt-4">
          <Button onClick={handleSave} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
            <Save className="w-4 h-4 mr-2" /> SAVE SETTINGS
          </Button>
        </motion.div>
      </CardContent>
    </Card>
  );
};

export default SettingsForm;
