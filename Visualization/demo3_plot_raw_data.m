function demo3_plot_raw_data(arduinoObj, frequency, UIAxes)


    % communication
    if isempty(arduinoObj) || ~isvalid(arduinoObj)
        error('Arduino connection is invalid.');
    end

    % Start streaming
    writeline(arduinoObj, "y"); 
    pause(1);
    baselineStr = readline(arduinoObj);
    baseline = str2num(baselineStr);

    accumulatedData = [];
    numFrames = 1000;

    % Plotting loop
    flush(arduinoObj);
    for i = 1:numFrames
        flush(arduinoObj);
        dataStr = readline(arduinoObj);
        data = str2num(dataStr);

        if ~isempty(data)
            accumulatedData = [accumulatedData; data];
            cla(UIAxes);
            plot(UIAxes, accumulatedData, Marker="o");
            xlim(UIAxes, [max([1, i-50]) max([i 50])]);
            title(UIAxes, sprintf("Live Frame %d", i));
            drawnow;
        end
    end

    disp("Plotting complete.");
end