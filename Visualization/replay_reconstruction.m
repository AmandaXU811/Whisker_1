function replay_reconstruction(rawPath, baselinePath)

epath = readlines("EIDORSpath.txt");
addpath(genpath(epath));
run(epath + "\startup.m");

% Resolve inputs
if nargin < 1 || strlength(string(rawPath)) == 0
    rawPath = findLatestCsv("eit_raw_");
else
    if ~isfile(rawPath)
        recordingsDir = resolveRecordingsDir();
        rawPath = fullfile(recordingsDir, "eit_raw_" + string(rawPath) + ".csv");
    end
end
if nargin < 2 || strlength(string(baselinePath)) == 0
    baselinePath = deriveBaselinePath(rawPath);
end

rawPath = char(rawPath);
baselinePath = char(baselinePath);

if ~isfile(rawPath)
    error("Raw CSV not found: " + rawPath);
end
if ~isfile(baselinePath)
    error("Baseline CSV not found: " + baselinePath);
end

disp("replay_reconstruction: raw = " + string(rawPath));
disp("replay_reconstruction: baseline = " + string(baselinePath));

baseline = readmatrix(baselinePath);
baseline = baseline(:).';

raw = readmatrix(rawPath);
if isempty(raw)
    error("Raw CSV is empty.");
end

% Remove rows that are all NaN
validRows = ~all(isnan(raw), 2);
raw = raw(validRows, :);

numFrames = size(raw, 1);
disp("replay_reconstruction: frames = " + numFrames);

%% ---------------- EIDORS MODEL ----------------
imdl = mk_common_model('d2d1c',16);
sim_img = mk_image(imdl.fwd_model,1);
stim = mk_stim_patterns(16, 1, '{ad}', '{ad}', {}, 1);
sim_img.fwd_model.stimulation = stim;

imdl.hyperparameter.value = 0.1;
imdl.RtR_prior = 'prior_laplace';

%% ---------------- PLOT SETUP ----------------
fig = figure('Name', 'Replay Reconstruction', 'Color', 'w');
ax1 = axes('Parent', fig);
ax2 = axes('Parent', fig);
set(ax1, 'Units', 'normalized', 'Position', [0.08 0.18 0.36 0.62]);
set(ax2, 'Units', 'normalized', 'Position', [0.56 0.18 0.36 0.62]);
ax1.Box = 'on';
ax2.Box = 'on';
ax1.XTick = [];
ax1.YTick = [];
fixed_clim = 0.2;

for i = 1:numFrames
    data = raw(i, :);
    if any(isnan(data)) || numel(data) ~= numel(baseline)
        continue
    end

    rec_img = inv_solve(imdl, fliplr(baseline).', fliplr(data).');
    rec_img.calc_colours.clim = fixed_clim;

    % Left: signal
    cla(ax1);
    sig = data(data~=0);
    plot(ax1, sig, 'b');
    ylim(ax1, [0 2]);
    if ~isempty(sig)
        xlim(ax1, [1 numel(sig)]);
    end
    title(ax1, sprintf('Frame %d', i));

    % Right: reconstruction
    delete(allchild(ax2));
    tempFig = figure('Visible','off');
    show_fem(rec_img, [1 0 0]);
    srcAxes = gca;
    copyobj(allchild(srcAxes), ax2);
    try
        colormap(ax2, colormap(srcAxes));
    catch
    end
    ax2.XLim = srcAxes.XLim;
    ax2.YLim = srcAxes.YLim;
    ax2.DataAspectRatio = [1 1 1];
    ax2.CLim = srcAxes.CLim;
    ax2.CLimMode = 'manual';
    colormap(ax2, 'parula');
    close(tempFig);
    title(ax2, 'Raw Data');

    drawnow limitrate;
end

end

function rawPath = findLatestCsv(prefix)
recordingsDir = resolveRecordingsDir();
if ~exist(recordingsDir, "dir")
    error("recordings folder not found: " + recordingsDir);
end

files = dir(fullfile(recordingsDir, prefix + "*.csv"));
if isempty(files)
    error("No files found with prefix " + prefix + " in " + recordingsDir);
end

[~, idx] = max([files.datenum]);
rawPath = fullfile(recordingsDir, files(idx).name);
end

function basePath = deriveBaselinePath(rawPath)
[folder, name, ~] = fileparts(rawPath);
baseName = strrep(name, "eit_raw_", "eit_baseline_");
basePath = fullfile(folder, baseName + ".csv");
end

function recordingsDir = resolveRecordingsDir()
% Prefer recordings folder next to this script
thisFile = mfilename('fullpath');
[thisDir, ~, ~] = fileparts(thisFile);
candidate = fullfile(thisDir, "recordings");
if exist(candidate, "dir")
    recordingsDir = candidate;
    return
end

% Fallback: if current folder is already recordings, use it
if endsWith(string(pwd), filesep + "recordings")
    recordingsDir = pwd;
    return
end

% Last resort: use recordings under current folder
recordingsDir = fullfile(pwd, "recordings");
end
